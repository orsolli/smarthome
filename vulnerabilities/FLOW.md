
```mermaid
graph LR
    %% Subgraphs
    subgraph File: __init__
        direction LR
        node_28810655["14: get_tree_parser_orchestrator()"]:::filled
        node_3406bcdf["20: merge_nix_trees()"]:::filled
    end
    subgraph File: __main__
        direction LR
        node_52c465ff["0: (global)()"]:::trunk
        node_18309179["6: main()"]:::filled
    end
    subgraph File: app
        direction LR
        node_1b5f246c["0: (global)()"]:::trunk
        node_6414887f["104: _store_tree_nodes()"]:::filled
        node_eac5024a["27: get_connection()"]:::filled
        node_c2d1df99["204: main()"]:::filled
        node_2dacb357["36: run_scan()"]:::filled
        node_b82a2a30["136: scan_endpoint()"]:::trunk
        node_fc6c3f3b["179: tree_endpoint()"]:::trunk
        node_62014776["153: vulnerabilities_endpoint()"]:::trunk
    end
    subgraph File: database
        direction LR
        node_6ae7213b["179: get_dependency_tree_for_scan()"]:::leaf
        node_67236daf["140: get_vulnerabilities_since()"]:::leaf
        node_3cd10037["47: init_db()"]:::leaf
        node_4507c78e["107: insert_dependency_node()"]:::leaf
        node_3e668c8c["62: insert_scan()"]:::leaf
        node_6239d11e["80: insert_vulnerability_event()"]:::leaf
    end
    subgraph File: formatter
        direction LR
        subgraph Class: TreeFormatterImpl
            direction LR
            node_22f13a39["63: _format_children()"]:::filled
            node_2d28bab3["40: _format_children_top_level()"]:::filled
            node_13b3cdca["6: generate_ascii_tree()"]:::filled
        end
        node_22f13a39["63: _format_children()"]:::filled
        node_2d28bab3["40: _format_children_top_level()"]:::filled
        node_13b3cdca["6: generate_ascii_tree()"]:::filled
    end
    subgraph File: generate_dependency_graph
        direction LR
        node_0584844b["0: (global)()"]:::trunk
        node_a6062961["4: generate_graph()"]:::leaf
    end
    subgraph File: interfaces
        direction LR
        subgraph Class: DerivationSource
            direction LR
            node_02f5eb2f["24: show_derivation()"]:::leaf
        end
        node_02f5eb2f["24: show_derivation()"]:::leaf
    end
    subgraph File: merger
        direction LR
        node_a77510b0["58: _dict_to_text()"]:::filled
        node_5c182e44["105: _parse_display_name()"]:::filled
        node_5765e9dc["131: _strip_tree_chars()"]:::leaf
        node_f3775b7e["78: _tree_to_dict()"]:::filled
        node_582d8624["42: _trees_to_text()"]:::filled
        node_e60741b4["16: merge_dependency_trees()"]:::filled
    end
    subgraph File: merger
        direction LR
        subgraph Class: TreeMergerImpl
            direction LR
            node_c4740bab["6: merge_trees()"]:::leaf
        end
        node_c4740bab["6: merge_trees()"]:::leaf
    end
    subgraph File: mock_derivation
        direction LR
        node_66264c3f["16: show_derivation()"]:::leaf
    end
    subgraph File: mock_vulnix
        direction LR
        node_5d91033e["42: scan_vulnerabilities()"]:::leaf
    end
    subgraph File: mock_why_depends
        direction LR
        node_9a903012["65: why_depends()"]:::leaf
    end
    subgraph File: normalizer
        direction LR
        node_6156d429["34: _find_vuln_info()"]:::filled
        node_121140ba["16: _severity_from_cvss()"]:::leaf
        node_4dbf6979["74: _traverse_tree()"]:::filled
        node_323366fe["51: normalize_tree()"]:::filled
    end
    subgraph File: orchestrator
        direction LR
        subgraph Class: TreeOrchestrator
            direction LR
            node_d06e084c["9: __init__()"]:::leaf
            node_304600a8["37: merge_nix_trees()"]:::trunk
            node_d397403b["17: process_tree_output()"]:::leaf
        end
        node_d06e084c["9: __init__()"]:::leaf
        node_304600a8["37: merge_nix_trees()"]:::trunk
        node_d397403b["17: process_tree_output()"]:::leaf
    end
    subgraph File: parser
        direction LR
        subgraph Class: TreeParserImpl
            direction LR
            node_e182b9e8["6: parse_tree_block()"]:::filled
            node_1c1a5343["52: split_into_trees()"]:::leaf
        end
        node_e182b9e8["6: parse_tree_block()"]:::filled
        node_1c1a5343["52: split_into_trees()"]:::leaf
    end
    subgraph File: scanner
        direction LR
        subgraph Class: MockDerivationSource
            direction LR
            node_8afd19b8["32: show_derivation()"]:::filled
        end
        subgraph Class: MockVulnerabilityScanner
            direction LR
            node_7f5618da["39: scan_vulnerabilities()"]:::filled
        end
        subgraph Class: MockDependencyMapper
            direction LR
            node_20d1c9a8["46: why_depends()"]:::filled
        end
        subgraph Class: TreeMergerImpl
            direction LR
            node_6f38014d["55: merge_trees()"]:::trunk
        end
        subgraph Class: TreeNormalizerImpl
            direction LR
            node_4e2c1ee8["66: __init__()"]:::leaf
            node_f20cba73["75: normalize()"]:::filled
        end
        subgraph Class: ScanPipeline
            direction LR
            node_6761b8a6["101: __init__()"]:::leaf
            node_8d0efd09["125: default()"]:::filled
            node_21491cc0["139: run_scan()"]:::leaf
        end
        node_20d1c9a8["46: why_depends()"]:::filled
        node_8afd19b8["32: show_derivation()"]:::filled
        node_7f5618da["39: scan_vulnerabilities()"]:::filled
        node_6761b8a6["101: __init__()"]:::leaf
        node_8d0efd09["125: default()"]:::filled
        node_21491cc0["139: run_scan()"]:::leaf
        node_6f38014d["55: merge_trees()"]:::trunk
        node_4e2c1ee8["66: __init__()"]:::leaf
        node_f20cba73["75: normalize()"]:::filled
    end
    subgraph File: test_app
        direction LR
        subgraph Class: TestRunScan
            direction LR
            node_264be787["91: test_scan_no_derivation_returns_error()"]:::trunk
            node_e5ece597["32: test_scan_returns_results()"]:::trunk
            node_4d5c867f["102: test_scan_stores_in_database()"]:::trunk
        end
        subgraph Class: TestStoreTreeNodes
            direction LR
            node_5c9f1bda["144: setUp()"]:::trunk
            node_5ec303de["189: test_skips_empty_node()"]:::trunk
            node_dc90c1f5["169: test_stores_nested_nodes()"]:::trunk
            node_dbf8fde2["157: test_stores_root_node()"]:::trunk
        end
        node_264be787["91: test_scan_no_derivation_returns_error()"]:::trunk
        node_e5ece597["32: test_scan_returns_results()"]:::trunk
        node_4d5c867f["102: test_scan_stores_in_database()"]:::trunk
        node_5c9f1bda["144: setUp()"]:::trunk
        node_5ec303de["189: test_skips_empty_node()"]:::trunk
        node_dc90c1f5["169: test_stores_nested_nodes()"]:::trunk
        node_dbf8fde2["157: test_stores_root_node()"]:::trunk
    end
    subgraph File: test_core_TestFormatter
        direction LR
        subgraph Class: TestFormatter
            direction LR
            node_c46f9baf["15: test_formatter_deep_tree()"]:::trunk
            node_ca2907aa["7: test_formatter_simple_tree()"]:::trunk
        end
        node_c46f9baf["15: test_formatter_deep_tree()"]:::trunk
        node_ca2907aa["7: test_formatter_simple_tree()"]:::trunk
    end
    subgraph File: test_core_TestMerger
        direction LR
        subgraph Class: TestMerger
            direction LR
            node_3e88b53b["33: test_merger_empty_trees()"]:::trunk
            node_a6e8dbd1["15: test_merger_multiple_trees_overlap()"]:::trunk
            node_67eeb0c0["7: test_merger_single_tree()"]:::trunk
        end
        node_3e88b53b["33: test_merger_empty_trees()"]:::trunk
        node_a6e8dbd1["15: test_merger_multiple_trees_overlap()"]:::trunk
        node_67eeb0c0["7: test_merger_single_tree()"]:::trunk
    end
    subgraph File: test_core_TestOrchestrator
        direction LR
        subgraph Class: TestOrchestrator
            direction LR
            node_1f29b1bb["8: test_orchestrator()"]:::trunk
            node_35f470c8["41: test_recursive_merge()"]:::trunk
        end
        node_1f29b1bb["8: test_orchestrator()"]:::trunk
        node_35f470c8["41: test_recursive_merge()"]:::trunk
    end
    subgraph File: test_core_TestParser
        direction LR
        subgraph Class: TestParser
            direction LR
            node_6a9b7a7f["39: test_complex_tree()"]:::trunk
            node_2b0c49f7["15: test_parse_tree_block()"]:::trunk
            node_b1a8bb0c["7: test_parser_split_logic()"]:::trunk
        end
        node_6a9b7a7f["39: test_complex_tree()"]:::trunk
        node_2b0c49f7["15: test_parse_tree_block()"]:::trunk
        node_b1a8bb0c["7: test_parser_split_logic()"]:::trunk
    end
    subgraph File: test_database
        direction LR
        subgraph Class: TestDatabase
            direction LR
            node_bcf4de5d["18: setUp()"]:::trunk
            node_9ee12ef6["86: test_get_dependency_tree_for_scan()"]:::trunk
            node_5e0e2ee8["77: test_get_vulnerabilities_since_filters_outside_range()"]:::trunk
            node_4739fd9e["57: test_get_vulnerabilities_since_returns_events()"]:::trunk
            node_343339d5["68: test_get_vulnerabilities_since_with_until()"]:::trunk
            node_7a06d0f4["49: test_insert_dependency_node_returns_id()"]:::trunk
            node_ff986288["36: test_insert_scan_returns_id()"]:::trunk
            node_5429eaea["41: test_insert_vulnerability_event_returns_id()"]:::trunk
        end
        node_bcf4de5d["18: setUp()"]:::trunk
        node_9ee12ef6["86: test_get_dependency_tree_for_scan()"]:::trunk
        node_5e0e2ee8["77: test_get_vulnerabilities_since_filters_outside_range()"]:::trunk
        node_4739fd9e["57: test_get_vulnerabilities_since_returns_events()"]:::trunk
        node_343339d5["68: test_get_vulnerabilities_since_with_until()"]:::trunk
        node_7a06d0f4["49: test_insert_dependency_node_returns_id()"]:::trunk
        node_ff986288["36: test_insert_scan_returns_id()"]:::trunk
        node_5429eaea["41: test_insert_vulnerability_event_returns_id()"]:::trunk
    end
    subgraph File: test_merger
        direction LR
        subgraph Class: TestDictToText
            direction LR
            node_ed7f9176["18: test_node_with_children()"]:::trunk
            node_bf9fb679["11: test_simple_node()"]:::trunk
        end
        subgraph Class: TestTreesToText
            direction LR
            node_0505cf7a["35: test_empty_list()"]:::trunk
            node_262cf684["46: test_multiple_trees()"]:::trunk
            node_589ab692["40: test_single_tree()"]:::trunk
        end
        subgraph Class: TestMergeDependencyTrees
            direction LR
            node_a2a507cd["58: test_empty_input()"]:::trunk
            node_64f31df8["81: test_multiple_trees()"]:::trunk
            node_789c879f["63: test_single_tree()"]:::trunk
        end
        node_ed7f9176["18: test_node_with_children()"]:::trunk
        node_bf9fb679["11: test_simple_node()"]:::trunk
        node_a2a507cd["58: test_empty_input()"]:::trunk
        node_64f31df8["81: test_multiple_trees()"]:::trunk
        node_789c879f["63: test_single_tree()"]:::trunk
        node_0505cf7a["35: test_empty_list()"]:::trunk
        node_262cf684["46: test_multiple_trees()"]:::trunk
        node_589ab692["40: test_single_tree()"]:::trunk
    end
    subgraph File: test_mock_derivation
        direction LR
        subgraph Class: TestMockDerivation
            direction LR
            node_05bb0ec2["14: test_metadata_is_empty_dict()"]:::trunk
            node_b39220db["8: test_returns_demo_derivation()"]:::trunk
        end
        node_05bb0ec2["14: test_metadata_is_empty_dict()"]:::trunk
        node_b39220db["8: test_returns_demo_derivation()"]:::trunk
    end
    subgraph File: test_normalizer
        direction LR
        subgraph Class: TestSeverityFromCvss
            direction LR
            node_c340381d["15: test_critical_score()"]:::trunk
            node_f1736b51["21: test_high_score()"]:::trunk
            node_5208d97c["33: test_low_score()"]:::trunk
            node_592f9455["27: test_medium_score()"]:::trunk
        end
        subgraph Class: TestFindVulnInfo
            direction LR
            node_7d6f7cf1["45: test_found_by_drv_path()"]:::trunk
            node_dc81920c["40: test_found_by_pname()"]:::trunk
            node_5f7b1856["50: test_not_found()"]:::trunk
        end
        subgraph Class: TestNormalizeTree
            direction LR
            node_c73963c7["74: test_clean_node()"]:::trunk
            node_729589d2["57: test_empty_tree()"]:::trunk
            node_97997967["84: test_nested_vulnerable_nodes()"]:::trunk
            node_a864cef7["62: test_vulnerable_node()"]:::trunk
        end
        node_7d6f7cf1["45: test_found_by_drv_path()"]:::trunk
        node_dc81920c["40: test_found_by_pname()"]:::trunk
        node_5f7b1856["50: test_not_found()"]:::trunk
        node_c73963c7["74: test_clean_node()"]:::trunk
        node_729589d2["57: test_empty_tree()"]:::trunk
        node_97997967["84: test_nested_vulnerable_nodes()"]:::trunk
        node_a864cef7["62: test_vulnerable_node()"]:::trunk
        node_c340381d["15: test_critical_score()"]:::trunk
        node_f1736b51["21: test_high_score()"]:::trunk
        node_5208d97c["33: test_low_score()"]:::trunk
        node_592f9455["27: test_medium_score()"]:::trunk
    end
    subgraph File: test_scanner
        direction LR
        subgraph Class: TestMockDerivationSource
            direction LR
            node_028aa681["25: test_show_derivation_returns_dict()"]:::trunk
        end
        subgraph Class: TestMockVulnerabilityScanner
            direction LR
            node_7476bb8f["36: test_scan_returns_vulnerabilities()"]:::trunk
        end
        subgraph Class: TestMockDependencyMapper
            direction LR
            node_d1ef7fa4["50: test_why_depends_returns_trees()"]:::trunk
        end
        subgraph Class: TestTreeMergerImpl
            direction LR
            node_e9ad6413["63: test_merge_empty_returns_empty()"]:::trunk
            node_bd545d58["69: test_merge_single_tree()"]:::trunk
        end
        subgraph Class: TestTreeNormalizerImpl
            direction LR
            node_95dafcad["110: test_normalize_empty_tree()"]:::trunk
            node_9d302ffe["93: test_normalize_with_custom_lookup()"]:::trunk
            node_d7938635["80: test_normalize_with_mock_lookup()"]:::trunk
        end
        subgraph Class: TestScanPipeline
            direction LR
            node_e536288f["120: test_default_creates_pipeline()"]:::trunk
            node_8771641f["140: test_run_scan_no_derivation_returns_error()"]:::trunk
            node_f3cfb59c["129: test_run_scan_returns_results()"]:::trunk
        end
        subgraph Class: TestScanPipelineWithCustomStages
            direction LR
            node_4862210e["154: test_run_scan_with_custom_stages()"]:::trunk
        end
        node_d1ef7fa4["50: test_why_depends_returns_trees()"]:::trunk
        node_028aa681["25: test_show_derivation_returns_dict()"]:::trunk
        node_7476bb8f["36: test_scan_returns_vulnerabilities()"]:::trunk
        node_e536288f["120: test_default_creates_pipeline()"]:::trunk
        node_8771641f["140: test_run_scan_no_derivation_returns_error()"]:::trunk
        node_f3cfb59c["129: test_run_scan_returns_results()"]:::trunk
        node_4862210e["154: test_run_scan_with_custom_stages()"]:::trunk
        node_e9ad6413["63: test_merge_empty_returns_empty()"]:::trunk
        node_bd545d58["69: test_merge_single_tree()"]:::trunk
        node_95dafcad["110: test_normalize_empty_tree()"]:::trunk
        node_9d302ffe["93: test_normalize_with_custom_lookup()"]:::trunk
        node_d7938635["80: test_normalize_with_mock_lookup()"]:::trunk
    end
    subgraph File: tree_utils
        direction LR
        node_db11b5b9["1: count_indent()"]:::leaf
        node_775d15c5["27: get_node_name()"]:::leaf
    end

    %% Edges
    node_28810655 --> node_d06e084c
    node_3406bcdf --> node_28810655
    node_52c465ff --> node_18309179
    node_18309179 --> node_3406bcdf
    node_1b5f246c --> node_c2d1df99
    node_6414887f --> node_6414887f
    node_6414887f --> node_4507c78e
    node_eac5024a --> node_3cd10037
    node_c2d1df99 --> node_eac5024a
    node_2dacb357 --> node_6414887f
    node_2dacb357 --> node_eac5024a
    node_2dacb357 --> node_3e668c8c
    node_2dacb357 --> node_6239d11e
    node_2dacb357 --> node_e60741b4
    node_2dacb357 --> node_66264c3f
    node_2dacb357 --> node_5d91033e
    node_2dacb357 --> node_9a903012
    node_2dacb357 --> node_323366fe
    node_b82a2a30 --> node_2dacb357
    node_fc6c3f3b --> node_eac5024a
    node_fc6c3f3b --> node_6ae7213b
    node_62014776 --> node_eac5024a
    node_62014776 --> node_67236daf
    node_22f13a39 --> node_22f13a39
    node_2d28bab3 --> node_22f13a39
    node_13b3cdca --> node_22f13a39
    node_13b3cdca --> node_2d28bab3
    node_0584844b --> node_a6062961
    node_a77510b0 --> node_a77510b0
    node_5c182e44 --> node_5765e9dc
    node_5c182e44 --> node_5765e9dc
    node_f3775b7e --> node_5c182e44
    node_f3775b7e --> node_f3775b7e
    node_582d8624 --> node_a77510b0
    node_e60741b4 --> node_3406bcdf
    node_e60741b4 --> node_f3775b7e
    node_e60741b4 --> node_582d8624
    node_6156d429 --> node_5d91033e
    node_4dbf6979 --> node_121140ba
    node_4dbf6979 --> node_4dbf6979
    node_323366fe --> node_4dbf6979
    node_304600a8 --> node_d397403b
    node_e182b9e8 --> node_db11b5b9
    node_e182b9e8 --> node_775d15c5
    node_20d1c9a8 --> node_9a903012
    node_8afd19b8 --> node_02f5eb2f
    node_7f5618da --> node_5d91033e
    node_8d0efd09 --> node_4e2c1ee8
    node_6f38014d --> node_e60741b4
    node_f20cba73 --> node_323366fe
    node_264be787 --> node_2dacb357
    node_e5ece597 --> node_2dacb357
    node_4d5c867f --> node_eac5024a
    node_4d5c867f --> node_2dacb357
    node_4d5c867f --> node_67236daf
    node_5c9f1bda --> node_eac5024a
    node_5c9f1bda --> node_3e668c8c
    node_5ec303de --> node_6414887f
    node_5ec303de --> node_6ae7213b
    node_dc90c1f5 --> node_6414887f
    node_dc90c1f5 --> node_6ae7213b
    node_dbf8fde2 --> node_6414887f
    node_dbf8fde2 --> node_6ae7213b
    node_c46f9baf --> node_13b3cdca
    node_ca2907aa --> node_13b3cdca
    node_3e88b53b --> node_c4740bab
    node_a6e8dbd1 --> node_c4740bab
    node_67eeb0c0 --> node_c4740bab
    node_1f29b1bb --> node_d06e084c
    node_35f470c8 --> node_d06e084c
    node_6a9b7a7f --> node_e182b9e8
    node_2b0c49f7 --> node_e182b9e8
    node_b1a8bb0c --> node_1c1a5343
    node_bcf4de5d --> node_3cd10037
    node_9ee12ef6 --> node_6ae7213b
    node_9ee12ef6 --> node_4507c78e
    node_9ee12ef6 --> node_3e668c8c
    node_5e0e2ee8 --> node_67236daf
    node_5e0e2ee8 --> node_3e668c8c
    node_5e0e2ee8 --> node_6239d11e
    node_4739fd9e --> node_67236daf
    node_4739fd9e --> node_3e668c8c
    node_4739fd9e --> node_6239d11e
    node_343339d5 --> node_67236daf
    node_343339d5 --> node_3e668c8c
    node_343339d5 --> node_6239d11e
    node_7a06d0f4 --> node_4507c78e
    node_7a06d0f4 --> node_3e668c8c
    node_ff986288 --> node_3e668c8c
    node_5429eaea --> node_3e668c8c
    node_5429eaea --> node_6239d11e
    node_ed7f9176 --> node_a77510b0
    node_bf9fb679 --> node_a77510b0
    node_a2a507cd --> node_e60741b4
    node_64f31df8 --> node_e60741b4
    node_789c879f --> node_e60741b4
    node_0505cf7a --> node_582d8624
    node_262cf684 --> node_582d8624
    node_589ab692 --> node_582d8624
    node_05bb0ec2 --> node_66264c3f
    node_b39220db --> node_66264c3f
    node_7d6f7cf1 --> node_6156d429
    node_dc81920c --> node_6156d429
    node_5f7b1856 --> node_6156d429
    node_c73963c7 --> node_323366fe
    node_729589d2 --> node_323366fe
    node_97997967 --> node_323366fe
    node_a864cef7 --> node_323366fe
    node_c340381d --> node_121140ba
    node_c340381d --> node_121140ba
    node_c340381d --> node_121140ba
    node_f1736b51 --> node_121140ba
    node_f1736b51 --> node_121140ba
    node_f1736b51 --> node_121140ba
    node_5208d97c --> node_121140ba
    node_5208d97c --> node_121140ba
    node_592f9455 --> node_121140ba
    node_592f9455 --> node_121140ba
    node_592f9455 --> node_121140ba
    node_d1ef7fa4 --> node_20d1c9a8
    node_028aa681 --> node_8afd19b8
    node_7476bb8f --> node_7f5618da
    node_e536288f --> node_8d0efd09
    node_8771641f --> node_8d0efd09
    node_f3cfb59c --> node_8d0efd09
    node_4862210e --> node_6761b8a6
    node_4862210e --> node_21491cc0
    node_e9ad6413 --> node_c4740bab
    node_bd545d58 --> node_c4740bab
    node_95dafcad --> node_4e2c1ee8
    node_95dafcad --> node_f20cba73
    node_9d302ffe --> node_4e2c1ee8
    node_9d302ffe --> node_f20cba73
    node_d7938635 --> node_4e2c1ee8
    node_d7938635 --> node_f20cba73

    %% Edge styles
    linkStyle 0 stroke:#0072B2
    linkStyle 1 stroke:#CC79A7
    linkStyle 2 stroke:#CC79A7
    linkStyle 3 stroke:#E69F00
    linkStyle 4 stroke:#F0E442
    linkStyle 5 stroke:#CC79A7
    linkStyle 6 stroke:#CC79A7
    linkStyle 7 stroke:#56B4E9
    linkStyle 8 stroke:#E69F00
    linkStyle 9 stroke:#CC79A7
    linkStyle 10 stroke:#CC79A7
    linkStyle 11 stroke:#CC79A7
    linkStyle 12 stroke:#CC79A7
    linkStyle 13 stroke:#CC79A7
    linkStyle 14 stroke:#CC79A7
    linkStyle 15 stroke:#CC79A7
    linkStyle 16 stroke:#CC79A7
    linkStyle 17 stroke:#CC79A7
    linkStyle 18 stroke:#000000
    linkStyle 19 stroke:#009E73
    linkStyle 20 stroke:#009E73
    linkStyle 21 stroke:#D55E00
    linkStyle 22 stroke:#D55E00
    linkStyle 23 stroke:#E69F00
    linkStyle 24 stroke:#009E73
    linkStyle 25 stroke:#56B4E9
    linkStyle 26 stroke:#56B4E9
    linkStyle 27 stroke:#009E73
    linkStyle 28 stroke:#000000
    linkStyle 29 stroke:#F0E442
    linkStyle 30 stroke:#F0E442
    linkStyle 31 stroke:#D55E00
    linkStyle 32 stroke:#D55E00
    linkStyle 33 stroke:#F0E442
    linkStyle 34 stroke:#F0E442
    linkStyle 35 stroke:#F0E442
    linkStyle 36 stroke:#F0E442
    linkStyle 37 stroke:#E69F00
    linkStyle 38 stroke:#E69F00
    linkStyle 39 stroke:#E69F00
    linkStyle 40 stroke:#D55E00
    linkStyle 41 stroke:#000000
    linkStyle 42 stroke:#000000
    linkStyle 43 stroke:#000000
    linkStyle 44 stroke:#000000
    linkStyle 45 stroke:#000000
    linkStyle 46 stroke:#56B4E9
    linkStyle 47 stroke:#E69F00
    linkStyle 48 stroke:#0072B2
    linkStyle 49 stroke:#009E73
    linkStyle 50 stroke:#CC79A7
    linkStyle 51 stroke:#CC79A7
    linkStyle 52 stroke:#CC79A7
    linkStyle 53 stroke:#CC79A7
    linkStyle 54 stroke:#CC79A7
    linkStyle 55 stroke:#56B4E9
    linkStyle 56 stroke:#56B4E9
    linkStyle 57 stroke:#D55E00
    linkStyle 58 stroke:#D55E00
    linkStyle 59 stroke:#0072B2
    linkStyle 60 stroke:#0072B2
    linkStyle 61 stroke:#56B4E9
    linkStyle 62 stroke:#56B4E9
    linkStyle 63 stroke:#CC79A7
    linkStyle 64 stroke:#56B4E9
    linkStyle 65 stroke:#009E73
    linkStyle 66 stroke:#E69F00
    linkStyle 67 stroke:#000000
    linkStyle 68 stroke:#009E73
    linkStyle 69 stroke:#000000
    linkStyle 70 stroke:#CC79A7
    linkStyle 71 stroke:#CC79A7
    linkStyle 72 stroke:#F0E442
    linkStyle 73 stroke:#0072B2
    linkStyle 74 stroke:#D55E00
    linkStyle 75 stroke:#D55E00
    linkStyle 76 stroke:#D55E00
    linkStyle 77 stroke:#000000
    linkStyle 78 stroke:#000000
    linkStyle 79 stroke:#000000
    linkStyle 80 stroke:#D55E00
    linkStyle 81 stroke:#D55E00
    linkStyle 82 stroke:#D55E00
    linkStyle 83 stroke:#0072B2
    linkStyle 84 stroke:#0072B2
    linkStyle 85 stroke:#0072B2
    linkStyle 86 stroke:#F0E442
    linkStyle 87 stroke:#F0E442
    linkStyle 88 stroke:#000000
    linkStyle 89 stroke:#56B4E9
    linkStyle 90 stroke:#56B4E9
    linkStyle 91 stroke:#D55E00
    linkStyle 92 stroke:#E69F00
    linkStyle 93 stroke:#0072B2
    linkStyle 94 stroke:#000000
    linkStyle 95 stroke:#CC79A7
    linkStyle 96 stroke:#56B4E9
    linkStyle 97 stroke:#F0E442
    linkStyle 98 stroke:#56B4E9
    linkStyle 99 stroke:#56B4E9
    linkStyle 100 stroke:#009E73
    linkStyle 101 stroke:#E69F00
    linkStyle 102 stroke:#F0E442
    linkStyle 103 stroke:#D55E00
    linkStyle 104 stroke:#CC79A7
    linkStyle 105 stroke:#56B4E9
    linkStyle 106 stroke:#CC79A7
    linkStyle 107 stroke:#CC79A7
    linkStyle 108 stroke:#0072B2
    linkStyle 109 stroke:#0072B2
    linkStyle 110 stroke:#0072B2
    linkStyle 111 stroke:#E69F00
    linkStyle 112 stroke:#E69F00
    linkStyle 113 stroke:#E69F00
    linkStyle 114 stroke:#F0E442
    linkStyle 115 stroke:#F0E442
    linkStyle 116 stroke:#0072B2
    linkStyle 117 stroke:#0072B2
    linkStyle 118 stroke:#0072B2
    linkStyle 119 stroke:#F0E442
    linkStyle 120 stroke:#E69F00
    linkStyle 121 stroke:#CC79A7
    linkStyle 122 stroke:#CC79A7
    linkStyle 123 stroke:#CC79A7
    linkStyle 124 stroke:#F0E442
    linkStyle 125 stroke:#D55E00
    linkStyle 126 stroke:#D55E00
    linkStyle 127 stroke:#009E73
    linkStyle 128 stroke:#000000
    linkStyle 129 stroke:#0072B2
    linkStyle 130 stroke:#0072B2
    linkStyle 131 stroke:#D55E00
    linkStyle 132 stroke:#D55E00
    linkStyle 133 stroke:#0072B2
    linkStyle 134 stroke:#0072B2

    %% Node styles
    classDef filled fill:#555555,stroke:#000000,stroke-width:2px;
    classDef leaf fill:#5555FF,stroke:#000000,stroke-width:2px;
    classDef trunk fill:#AA5555,stroke:#000000,stroke-width:2px;
```