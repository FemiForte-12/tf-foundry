import unittest
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import time

class TestEFSCSIDriver(unittest.TestCase):
    def setUp(self):
        # Load kube config
        try:
            config.load_kube_config()
        except:
            config.load_incluster_config()
        
        self.v1 = client.CoreV1Api()
        self.storage_v1 = client.StorageV1Api()
        self.apps_v1 = client.AppsV1Api()
        
        # Test namespace
        self.namespace = "efs-test"
        
    def tearDown(self):
        # Cleanup resources after tests
        try:
            self.v1.delete_namespace(self.namespace)
        except ApiException:
            pass

    def test_efs_csi_driver_deployment(self):
        """Test if EFS CSI driver deployment is running"""
        try:
            deployment = self.apps_v1.read_namespaced_deployment(
                name="efs-csi-controller",
                namespace="kube-system"
            )
            self.assertIsNotNone(deployment)
            self.assertTrue(deployment.status.ready_replicas > 0)
        except ApiException as e:
            self.fail(f"EFS CSI driver deployment not found: {e}")

    def test_storage_class_creation(self):
        """Test creation of EFS StorageClass"""
        storage_class = client.V1StorageClass(
            api_version="storage.k8s.io/v1",
            kind="StorageClass",
            metadata=client.V1ObjectMeta(name="efs-sc"),
            provisioner="efs.csi.aws.com"
        )

        try:
            response = self.storage_v1.create_storage_class(storage_class)
            self.assertEqual(response.metadata.name, "efs-sc")
        except ApiException as e:
            self.fail(f"Failed to create StorageClass: {e}")
        finally:
            try:
                self.storage_v1.delete_storage_class("efs-sc")
            except ApiException:
                pass

    def test_pvc_creation(self):
        """Test creation of PVC using EFS storage class"""
        # Create namespace
        namespace = client.V1Namespace(metadata=client.V1ObjectMeta(name=self.namespace))
        self.v1.create_namespace(namespace)

        # Create PVC
        pvc = client.V1PersistentVolumeClaim(
            metadata=client.V1ObjectMeta(name="efs-pvc", namespace=self.namespace),
            spec=client.V1PersistentVolumeClaimSpec(
                access_modes=["ReadWriteMany"],
                storage_class_name="efs-sc",
                resources=client.V1ResourceRequirements(
                    requests={"storage": "5Gi"}
                )
            )
        )

        try:
            response = self.v1.create_namespaced_persistent_volume_claim(
                namespace=self.namespace,
                body=pvc
            )
            self.assertEqual(response.metadata.name, "efs-pvc")
            
            # Wait for PVC to be bound
            max_retries = 10
            for _ in range(max_retries):
                pvc_status = self.v1.read_namespaced_persistent_volume_claim_status(
                    name="efs-pvc",
                    namespace=self.namespace
                )
                if pvc_status.status.phase == "Bound":
                    break
                time.sleep(5)
            
            self.assertEqual(pvc_status.status.phase, "Bound")
            
        except ApiException as e:
            self.fail(f"Failed to create PVC: {e}")

    def test_pod_with_efs_volume(self):
        """Test pod creation with EFS volume mount"""
        pod = client.V1Pod(
            metadata=client.V1ObjectMeta(name="efs-test-pod", namespace=self.namespace),
            spec=client.V1PodSpec(
                containers=[
                    client.V1Container(
                        name="test-container",
                        image="nginx",
                        volume_mounts=[
                            client.V1VolumeMount(
                                name="efs-volume",
                                mount_path="/data"
                            )
                        ]
                    )
                ],
                volumes=[
                    client.V1Volume(
                        name="efs-volume",
                        persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(
                            claim_name="efs-pvc"
                        )
                    )
                ]
            )
        )

        try:
            response = self.v1.create_namespaced_pod(
                namespace=self.namespace,
                body=pod
            )
            self.assertEqual(response.metadata.name, "efs-test-pod")
            
            # Wait for pod to be running
            max_retries = 10
            for _ in range(max_retries):
                pod_status = self.v1.read_namespaced_pod_status(
                    name="efs-test-pod",
                    namespace=self.namespace
                )
                if pod_status.status.phase == "Running":
                    break
                time.sleep(5)
            
            self.assertEqual(pod_status.status.phase, "Running")
            
        except ApiException as e:
            self.fail(f"Failed to create pod with EFS volume: {e}")

    def test_storage_class_exists(self):
        """Test if EFS StorageClass exists and is properly configured"""
        try:
            storage_class = self.storage_v1.read_storage_class(name="efs-sc")
            self.assertEqual(storage_class.metadata.name, "efs-sc")
            self.assertEqual(storage_class.provisioner, "efs.csi.aws.com")
        except ApiException as e:
            self.fail(f"EFS StorageClass not found or incorrectly configured: {e}")

    def test_pvc_exists(self):
        """Test if PVC exists and is bound"""
        try:
            pvc_status = self.v1.read_namespaced_persistent_volume_claim_status(
                name="efs-pvc",
                namespace=self.namespace
            )
            self.assertEqual(pvc_status.metadata.name, "efs-pvc")
            self.assertEqual(pvc_status.status.phase, "Bound")
            self.assertEqual(pvc_status.spec.storage_class_name, "efs-sc")
            self.assertIn("ReadWriteMany", pvc_status.spec.access_modes)
        except ApiException as e:
            self.fail(f"EFS PVC not found or incorrectly configured: {e}")

    def test_pod_with_efs_volume_exists(self):
        """Test if pod with EFS volume exists and is running"""
        try:
            pod = self.v1.read_namespaced_pod(
                name="efs-test-pod",
                namespace=self.namespace
            )
            self.assertEqual(pod.metadata.name, "efs-test-pod")
            self.assertEqual(pod.status.phase, "Running")
            
            # Verify volume configuration
            efs_volume = next(
                (vol for vol in pod.spec.volumes if vol.name == "efs-volume"), 
                None
            )
            self.assertIsNotNone(efs_volume)
            self.assertEqual(
                efs_volume.persistent_volume_claim.claim_name,
                "efs-pvc"
            )
            
            # Verify volume mount in container
            container = pod.spec.containers[0]
            efs_mount = next(
                (mount for mount in container.volume_mounts if mount.name == "efs-volume"),
                None
            )
            self.assertIsNotNone(efs_mount)
            self.assertEqual(efs_mount.mount_path, "/data")
            
        except ApiException as e:
            self.fail(f"Pod with EFS volume not found or incorrectly configured: {e}")

if __name__ == '__main__':
    unittest.main()
