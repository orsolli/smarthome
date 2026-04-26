"""Tests for pipeline interface definitions."""

import unittest

from interfaces import (
    DependencyMapper,
    DerivationSource,
    TreeMerger,
    TreeNormalizer,
    VulnerabilityScanner,
)


class TestDerivationSourceInterface(unittest.TestCase):
    """Test that DerivationSource is an abstract base class."""

    def test_is_abstract(self):
        """DerivationSource cannot be instantiated directly."""
        with self.assertRaises(TypeError):
            DerivationSource()

    def test_has_show_derivation(self):
        """DerivationSource defines show_derivation method."""
        self.assertTrue(hasattr(DerivationSource, "show_derivation"))


class TestVulnerabilityScannerInterface(unittest.TestCase):
    """Test that VulnerabilityScanner is an abstract base class."""

    def test_is_abstract(self):
        """VulnerabilityScanner cannot be instantiated directly."""
        with self.assertRaises(TypeError):
            VulnerabilityScanner()

    def test_has_scan_vulnerabilities(self):
        """VulnerabilityScanner defines scan_vulnerabilities method."""
        self.assertTrue(hasattr(VulnerabilityScanner, "scan_vulnerabilities"))


class TestDependencyMapperInterface(unittest.TestCase):
    """Test that DependencyMapper is an abstract base class."""

    def test_is_abstract(self):
        """DependencyMapper cannot be instantiated directly."""
        with self.assertRaises(TypeError):
            DependencyMapper()

    def test_has_why_depends(self):
        """DependencyMapper defines why_depends method."""
        self.assertTrue(hasattr(DependencyMapper, "why_depends"))


class TestTreeMergerInterface(unittest.TestCase):
    """Test that TreeMerger is an abstract base class."""

    def test_is_abstract(self):
        """TreeMerger cannot be instantiated directly."""
        with self.assertRaises(TypeError):
            TreeMerger()

    def test_has_merge_trees(self):
        """TreeMerger defines merge_trees method."""
        self.assertTrue(hasattr(TreeMerger, "merge_trees"))


class TestTreeNormalizerInterface(unittest.TestCase):
    """Test that TreeNormalizer is an abstract base class."""

    def test_is_abstract(self):
        """TreeNormalizer cannot be instantiated directly."""
        with self.assertRaises(TypeError):
            TreeNormalizer()

    def test_has_normalize(self):
        """TreeNormalizer defines normalize method."""
        self.assertTrue(hasattr(TreeNormalizer, "normalize"))


if __name__ == "__main__":
    unittest.main()
