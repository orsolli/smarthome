"""Tests for pipeline interface definitions."""

import unittest

from interfaces import (
    DependencyMapperInterface,
    DerivationSourceInterface,
    StorageInterface,
    TreeMergerInterface,
    TreeNormalizerInterface,
    VulnerabilityScannerInterface,
)


class TestDerivationSourceInterface(unittest.TestCase):
    """Test that DerivationSource is an abstract base class."""

    def test_is_abstract(self):
        """DerivationSourceInterface cannot be instantiated directly."""
        with self.assertRaises(TypeError):
            DerivationSourceInterface()

    def test_has_show_derivation(self):
        """DerivationSource defines show_derivation method."""
        self.assertTrue(hasattr(DerivationSourceInterface, "show_derivation"))


class TestVulnerabilityScannerInterface(unittest.TestCase):
    """Test that VulnerabilityScanner is an abstract base class."""

    def test_is_abstract(self):
        """VulnerabilityScannerInterface cannot be instantiated directly."""
        with self.assertRaises(TypeError):
            VulnerabilityScannerInterface()

    def test_has_scan_vulnerabilities(self):
        """VulnerabilityScanner defines scan_vulnerabilities method."""
        self.assertTrue(hasattr(VulnerabilityScannerInterface, "scan_vulnerabilities"))


class TestDependencyMapperInterface(unittest.TestCase):
    """Test that DependencyMapper is an abstract base class."""

    def test_is_abstract(self):
        """DependencyMapperInterface cannot be instantiated directly."""
        with self.assertRaises(TypeError):
            DependencyMapperInterface()

    def test_has_why_depends(self):
        """DependencyMapper defines why_depends method."""
        self.assertTrue(hasattr(DependencyMapperInterface, "why_depends"))


class TestTreeMergerInterface(unittest.TestCase):
    """Test that TreeMerger is an abstract base class."""

    def test_is_abstract(self):
        """TreeMergerInterface cannot be instantiated directly."""
        with self.assertRaises(TypeError):
            TreeMergerInterface()

    def test_has_merge_trees(self):
        """TreeMerger defines merge_trees method."""
        self.assertTrue(hasattr(TreeMergerInterface, "merge_trees"))


class TestTreeNormalizerInterface(unittest.TestCase):
    """Test that TreeNormalizer is an abstract base class."""

    def test_is_abstract(self):
        """TreeNormalizer cannot be instantiated directly."""
        with self.assertRaises(TypeError):
            TreeNormalizerInterface()

    def test_has_normalize(self):
        """TreeNormalizer defines normalize method."""
        self.assertTrue(hasattr(TreeNormalizerInterface, "normalize"))


class TestStorageInterface(unittest.TestCase):
    """Test that StorageInterface is an abstract base class."""

    def test_is_abstract(self):
        """StorageInterface cannot be instantiated directly."""
        with self.assertRaises(TypeError):
            StorageInterface()

    def test_has_insert_scan(self):
        """StorageInterface defines insert_scan method."""
        self.assertTrue(hasattr(StorageInterface, "insert_scan"))

    def test_has_insert_vulnerability_event(self):
        """StorageInterface defines insert_vulnerability_event method."""
        self.assertTrue(hasattr(StorageInterface, "insert_vulnerability_event"))

    def test_has_insert_dependency_node(self):
        """StorageInterface defines insert_dependency_node method."""
        self.assertTrue(hasattr(StorageInterface, "insert_dependency_node"))

    def test_has_update_dependency_node(self):
        """StorageInterface defines update_dependency_node method."""
        self.assertTrue(hasattr(StorageInterface, "update_dependency_node"))


if __name__ == "__main__":
    import sys
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    unittest.main()
