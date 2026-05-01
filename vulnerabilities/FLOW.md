
```mermaid
graph LR
    %% Subgraphs
    subgraph File: __main__
        direction LR
        node___main___global_986["0: (global)()"]:::trunk
        node___main___get_tree_parser_orchestrator_1d0["17: get_tree_parser_orchestrator()"]:::filled
        node___main___main_f54["27: main()"]:::filled
        node___main___merge_nix_trees_c57["23: merge_nix_trees()"]:::filled
    end
    subgraph File: app
        direction LR
        node_app_global_897["0: (global)()"]:::trunk
        node_app_main_9c5["117: main()"]:::filled
        node_app_run_scan_0f4["28: run_scan()"]:::filled
        node_app_scan_endpoint_42a["49: scan_endpoint()"]:::trunk
        node_app_tree_endpoint_060["92: tree_endpoint()"]:::trunk
        node_app_vulnerabilities_endpoint_aa6["66: vulnerabilities_endpoint()"]:::trunk
    end
    subgraph File: database
        direction LR
        node_database_get_dependency_tree_for_scan_426["179: get_dependency_tree_for_scan()"]:::leaf
        node_database_get_vulnerabilities_since_ea4["140: get_vulnerabilities_since()"]:::leaf
        node_database_init_db_6e2["47: init_db()"]:::leaf
        node_database_insert_dependency_node_4a2["107: insert_dependency_node()"]:::leaf
        node_database_insert_scan_500["62: insert_scan()"]:::leaf
        node_database_insert_vulnerability_event_09d["80: insert_vulnerability_event()"]:::leaf
    end
    subgraph File: database_storage
        direction LR
        subgraph Class: DatabaseStorage
            direction LR
            node_DatabaseStorage___init___8bc["21: __init__()"]:::leaf
        end
        node_DatabaseStorage___init___8bc["21: __init__()"]:::leaf
    end
    subgraph File: formatter
        direction LR
        subgraph Class: TreeFormatterImpl
            direction LR
            node_TreeFormatterImpl__format_children_32b["63: _format_children()"]:::filled
            node_TreeFormatterImpl__format_children_top_level_558["40: _format_children_top_level()"]:::filled
            node_TreeFormatterImpl_generate_ascii_tree_d79["6: generate_ascii_tree()"]:::filled
        end
        node_TreeFormatterImpl__format_children_32b["63: _format_children()"]:::filled
        node_TreeFormatterImpl__format_children_top_level_558["40: _format_children_top_level()"]:::filled
        node_TreeFormatterImpl_generate_ascii_tree_d79["6: generate_ascii_tree()"]:::filled
    end
    subgraph File: merger
        direction LR
        subgraph Class: TreeMergerImpl
            direction LR
            node_TreeMergerImpl_merge_trees_40c["122: merge_trees()"]:::leaf
        end
        node_TreeMergerImpl_merge_trees_40c["122: merge_trees()"]:::leaf
        node_merger__dict_to_text_5ab["32: _dict_to_text()"]:::filled
        node_merger__parse_display_name_ff8["79: _parse_display_name()"]:::filled
        node_merger__strip_tree_chars_2ad["105: _strip_tree_chars()"]:::leaf
        node_merger__tree_to_dict_200["52: _tree_to_dict()"]:::filled
        node_merger__trees_to_text_bca["16: _trees_to_text()"]:::filled
    end
    subgraph File: mock_derivation
        direction LR
        subgraph Class: MockDerivationSource
            direction LR
            node_MockDerivationSource_show_derivation_529["20: show_derivation()"]:::leaf
        end
        node_MockDerivationSource_show_derivation_529["20: show_derivation()"]:::leaf
    end
    subgraph File: mock_vulnix
        direction LR
        subgraph Class: MockVulnerabilityScanner
            direction LR
            node_MockVulnerabilityScanner_scan_vulnerabilities_10c["47: scan_vulnerabilities()"]:::leaf
        end
        node_MockVulnerabilityScanner_scan_vulnerabilities_10c["47: scan_vulnerabilities()"]:::leaf
    end
    subgraph File: mock_why_depends
        direction LR
        subgraph Class: MockDependencyMapper
            direction LR
            node_MockDependencyMapper_why_depends_ea8["32: why_depends()"]:::leaf
        end
        node_MockDependencyMapper_why_depends_ea8["32: why_depends()"]:::leaf
    end
    subgraph File: normalizer
        direction LR
        subgraph Class: TreeNormalizerImpl
            direction LR
            node_TreeNormalizerImpl_normalize_d22["41: normalize()"]:::filled
        end
        node_TreeNormalizerImpl_normalize_d22["41: normalize()"]:::filled
        node_normalizer__severity_from_cvss_86f["16: _severity_from_cvss()"]:::leaf
        node_normalizer__traverse_tree_537["61: _traverse_tree()"]:::filled
    end
    subgraph File: orchestrator
        direction LR
        subgraph Class: TreeOrchestrator
            direction LR
            node_TreeOrchestrator___init___d80["9: __init__()"]:::leaf
        end
        node_TreeOrchestrator___init___d80["9: __init__()"]:::leaf
    end
    subgraph File: parser
        direction LR
        subgraph Class: TreeParserImpl
            direction LR
            node_TreeParserImpl_parse_tree_block_b90["6: parse_tree_block()"]:::filled
            node_TreeParserImpl_split_into_trees_c6f["52: split_into_trees()"]:::leaf
        end
        node_TreeParserImpl_parse_tree_block_b90["6: parse_tree_block()"]:::filled
        node_TreeParserImpl_split_into_trees_c6f["52: split_into_trees()"]:::leaf
    end
    subgraph File: scanner
        direction LR
        subgraph Class: MockStorage
            direction LR
            node_MockStorage___init___3fb["34: __init__()"]:::leaf
            node_MockStorage__next_id_31b["40: _next_id()"]:::leaf
            node_MockStorage_insert_dependency_node_000["63: insert_dependency_node()"]:::filled
            node_MockStorage_insert_scan_69c["45: insert_scan()"]:::filled
            node_MockStorage_insert_vulnerability_event_e4d["50: insert_vulnerability_event()"]:::filled
        end
        subgraph Class: ScanPipeline
            direction LR
            node_ScanPipeline___init___136["101: __init__()"]:::leaf
            node_ScanPipeline__store_tree_nodes_e80["213: _store_tree_nodes()"]:::filled
            node_ScanPipeline_default_ef1["128: default()"]:::trunk
            node_ScanPipeline_run_scan_d6e["147: run_scan()"]:::filled
        end
        node_MockStorage___init___3fb["34: __init__()"]:::leaf
        node_MockStorage__next_id_31b["40: _next_id()"]:::leaf
        node_MockStorage_insert_dependency_node_000["63: insert_dependency_node()"]:::filled
        node_MockStorage_insert_scan_69c["45: insert_scan()"]:::filled
        node_MockStorage_insert_vulnerability_event_e4d["50: insert_vulnerability_event()"]:::filled
        node_ScanPipeline___init___136["101: __init__()"]:::leaf
        node_ScanPipeline__store_tree_nodes_e80["213: _store_tree_nodes()"]:::filled
        node_ScanPipeline_default_ef1["128: default()"]:::trunk
        node_ScanPipeline_run_scan_d6e["147: run_scan()"]:::filled
    end
    subgraph File: test_core_TestFormatter
        direction LR
        subgraph Class: TestFormatter
            direction LR
            node_TestFormatter_test_formatter_deep_tree_08b["14: test_formatter_deep_tree()"]:::trunk
            node_TestFormatter_test_formatter_simple_tree_acd["7: test_formatter_simple_tree()"]:::trunk
        end
        node_TestFormatter_test_formatter_deep_tree_08b["14: test_formatter_deep_tree()"]:::trunk
        node_TestFormatter_test_formatter_simple_tree_acd["7: test_formatter_simple_tree()"]:::trunk
    end
    subgraph File: test_core_TestMerger
        direction LR
        subgraph Class: TestMerger
            direction LR
            node_TestMerger_test_merger_empty_trees_b5b["33: test_merger_empty_trees()"]:::trunk
            node_TestMerger_test_merger_multiple_trees_overlap_48e["15: test_merger_multiple_trees_overlap()"]:::trunk
            node_TestMerger_test_merger_single_tree_7d9["7: test_merger_single_tree()"]:::trunk
        end
        node_TestMerger_test_merger_empty_trees_b5b["33: test_merger_empty_trees()"]:::trunk
        node_TestMerger_test_merger_multiple_trees_overlap_48e["15: test_merger_multiple_trees_overlap()"]:::trunk
        node_TestMerger_test_merger_single_tree_7d9["7: test_merger_single_tree()"]:::trunk
    end
    subgraph File: test_core_TestOrchestrator
        direction LR
        subgraph Class: TestOrchestrator
            direction LR
            node_TestOrchestrator_test_orchestrator_e63["8: test_orchestrator()"]:::trunk
            node_TestOrchestrator_test_recursive_merge_718["41: test_recursive_merge()"]:::trunk
        end
        node_TestOrchestrator_test_orchestrator_e63["8: test_orchestrator()"]:::trunk
        node_TestOrchestrator_test_recursive_merge_718["41: test_recursive_merge()"]:::trunk
    end
    subgraph File: test_core_TestParser
        direction LR
        subgraph Class: TestParser
            direction LR
            node_TestParser_test_complex_tree_164["42: test_complex_tree()"]:::trunk
            node_TestParser_test_parse_tree_block_487["18: test_parse_tree_block()"]:::trunk
            node_TestParser_test_parser_split_logic_294["10: test_parser_split_logic()"]:::trunk
        end
        node_TestParser_test_complex_tree_164["42: test_complex_tree()"]:::trunk
        node_TestParser_test_parse_tree_block_487["18: test_parse_tree_block()"]:::trunk
        node_TestParser_test_parser_split_logic_294["10: test_parser_split_logic()"]:::trunk
    end
    subgraph File: test_database
        direction LR
        subgraph Class: TestDatabase
            direction LR
            node_TestDatabase_setUp_f4a["18: setUp()"]:::trunk
            node_TestDatabase_test_get_dependency_tree_for_scan_5e9["86: test_get_dependency_tree_for_scan()"]:::trunk
            node_TestDatabase_test_get_vulnerabilities_since_filters_outside_range_784["77: test_get_vulnerabilities_since_filters_outside_range()"]:::trunk
            node_TestDatabase_test_get_vulnerabilities_since_returns_events_d33["57: test_get_vulnerabilities_since_returns_events()"]:::trunk
            node_TestDatabase_test_get_vulnerabilities_since_with_until_171["68: test_get_vulnerabilities_since_with_until()"]:::trunk
            node_TestDatabase_test_insert_dependency_node_returns_id_5d4["49: test_insert_dependency_node_returns_id()"]:::trunk
            node_TestDatabase_test_insert_scan_returns_id_f78["36: test_insert_scan_returns_id()"]:::trunk
            node_TestDatabase_test_insert_vulnerability_event_returns_id_5bd["41: test_insert_vulnerability_event_returns_id()"]:::trunk
        end
        node_TestDatabase_setUp_f4a["18: setUp()"]:::trunk
        node_TestDatabase_test_get_dependency_tree_for_scan_5e9["86: test_get_dependency_tree_for_scan()"]:::trunk
        node_TestDatabase_test_get_vulnerabilities_since_filters_outside_range_784["77: test_get_vulnerabilities_since_filters_outside_range()"]:::trunk
        node_TestDatabase_test_get_vulnerabilities_since_returns_events_d33["57: test_get_vulnerabilities_since_returns_events()"]:::trunk
        node_TestDatabase_test_get_vulnerabilities_since_with_until_171["68: test_get_vulnerabilities_since_with_until()"]:::trunk
        node_TestDatabase_test_insert_dependency_node_returns_id_5d4["49: test_insert_dependency_node_returns_id()"]:::trunk
        node_TestDatabase_test_insert_scan_returns_id_f78["36: test_insert_scan_returns_id()"]:::trunk
        node_TestDatabase_test_insert_vulnerability_event_returns_id_5bd["41: test_insert_vulnerability_event_returns_id()"]:::trunk
    end
    subgraph File: test_merger
        direction LR
        subgraph Class: TestDictToText
            direction LR
            node_TestDictToText_test_node_with_children_926["18: test_node_with_children()"]:::trunk
            node_TestDictToText_test_simple_node_157["11: test_simple_node()"]:::trunk
        end
        subgraph Class: TestTreesToText
            direction LR
            node_TestTreesToText_test_empty_list_9b0["35: test_empty_list()"]:::trunk
            node_TestTreesToText_test_multiple_trees_1ef["46: test_multiple_trees()"]:::trunk
            node_TestTreesToText_test_single_tree_9d9["40: test_single_tree()"]:::trunk
        end
        node_TestDictToText_test_node_with_children_926["18: test_node_with_children()"]:::trunk
        node_TestDictToText_test_simple_node_157["11: test_simple_node()"]:::trunk
        node_TestTreesToText_test_empty_list_9b0["35: test_empty_list()"]:::trunk
        node_TestTreesToText_test_multiple_trees_1ef["46: test_multiple_trees()"]:::trunk
        node_TestTreesToText_test_single_tree_9d9["40: test_single_tree()"]:::trunk
    end
    subgraph File: test_normalizer
        direction LR
        subgraph Class: TestSeverityFromCvss
            direction LR
            node_TestSeverityFromCvss_test_critical_score_9e1["13: test_critical_score()"]:::trunk
            node_TestSeverityFromCvss_test_high_score_47d["19: test_high_score()"]:::trunk
            node_TestSeverityFromCvss_test_low_score_43e["31: test_low_score()"]:::trunk
            node_TestSeverityFromCvss_test_medium_score_8b4["25: test_medium_score()"]:::trunk
        end
        subgraph Class: TestNormalizeTree
            direction LR
            node_TestNormalizeTree_setUp_89e["45: setUp()"]:::trunk
        end
        node_TestNormalizeTree_setUp_89e["45: setUp()"]:::trunk
        node_TestSeverityFromCvss_test_critical_score_9e1["13: test_critical_score()"]:::trunk
        node_TestSeverityFromCvss_test_high_score_47d["19: test_high_score()"]:::trunk
        node_TestSeverityFromCvss_test_low_score_43e["31: test_low_score()"]:::trunk
        node_TestSeverityFromCvss_test_medium_score_8b4["25: test_medium_score()"]:::trunk
        node_test_normalizer__make_vuln_lookup_9a5["37: _make_vuln_lookup()"]:::leaf
    end
    subgraph File: test_scanner
        direction LR
        subgraph Class: TestMockDerivationSource
            direction LR
            node_TestMockDerivationSource_test_show_derivation_returns_dict_93f["31: test_show_derivation_returns_dict()"]:::trunk
        end
        subgraph Class: TestMockVulnerabilityScanner
            direction LR
            node_TestMockVulnerabilityScanner_test_scan_returns_vulnerabilities_b1f["42: test_scan_returns_vulnerabilities()"]:::trunk
        end
        subgraph Class: TestMockDependencyMapper
            direction LR
            node_TestMockDependencyMapper_test_why_depends_returns_trees_73d["56: test_why_depends_returns_trees()"]:::trunk
        end
        subgraph Class: TestTreeMergerImpl
            direction LR
            node_TestTreeMergerImpl_test_merge_empty_returns_empty_481["69: test_merge_empty_returns_empty()"]:::trunk
            node_TestTreeMergerImpl_test_merge_single_tree_047["75: test_merge_single_tree()"]:::trunk
        end
        subgraph Class: TestTreeNormalizerImpl
            direction LR
            node_TestTreeNormalizerImpl__make_vuln_map_246["86: _make_vuln_map()"]:::leaf
            node_TestTreeNormalizerImpl_test_normalize_empty_tree_115["120: test_normalize_empty_tree()"]:::trunk
            node_TestTreeNormalizerImpl_test_normalize_with_custom_lookup_847["104: test_normalize_with_custom_lookup()"]:::trunk
            node_TestTreeNormalizerImpl_test_normalize_with_mock_lookup_9f8["89: test_normalize_with_mock_lookup()"]:::trunk
        end
        subgraph Class: TestMockStorage
            direction LR
            node_TestMockStorage_test_insert_dependency_node_74d["148: test_insert_dependency_node()"]:::trunk
            node_TestMockStorage_test_insert_scan_b7a["130: test_insert_scan()"]:::trunk
            node_TestMockStorage_test_insert_vulnerability_event_874["138: test_insert_vulnerability_event()"]:::trunk
        end
        subgraph Class: TestScanPipelineWithCustomStages
            direction LR
            node_TestScanPipelineWithCustomStages_test_run_scan_with_custom_stages_7f0["193: test_run_scan_with_custom_stages()"]:::trunk
        end
        node_TestMockDependencyMapper_test_why_depends_returns_trees_73d["56: test_why_depends_returns_trees()"]:::trunk
        node_TestMockDerivationSource_test_show_derivation_returns_dict_93f["31: test_show_derivation_returns_dict()"]:::trunk
        node_TestMockStorage_test_insert_dependency_node_74d["148: test_insert_dependency_node()"]:::trunk
        node_TestMockStorage_test_insert_scan_b7a["130: test_insert_scan()"]:::trunk
        node_TestMockStorage_test_insert_vulnerability_event_874["138: test_insert_vulnerability_event()"]:::trunk
        node_TestMockVulnerabilityScanner_test_scan_returns_vulnerabilities_b1f["42: test_scan_returns_vulnerabilities()"]:::trunk
        node_TestScanPipelineWithCustomStages_test_run_scan_with_custom_stages_7f0["193: test_run_scan_with_custom_stages()"]:::trunk
        node_TestTreeMergerImpl_test_merge_empty_returns_empty_481["69: test_merge_empty_returns_empty()"]:::trunk
        node_TestTreeMergerImpl_test_merge_single_tree_047["75: test_merge_single_tree()"]:::trunk
        node_TestTreeNormalizerImpl__make_vuln_map_246["86: _make_vuln_map()"]:::leaf
        node_TestTreeNormalizerImpl_test_normalize_empty_tree_115["120: test_normalize_empty_tree()"]:::trunk
        node_TestTreeNormalizerImpl_test_normalize_with_custom_lookup_847["104: test_normalize_with_custom_lookup()"]:::trunk
        node_TestTreeNormalizerImpl_test_normalize_with_mock_lookup_9f8["89: test_normalize_with_mock_lookup()"]:::trunk
    end
    subgraph File: tree_utils
        direction LR
        node_tree_utils_count_indent_2c7["1: count_indent()"]:::leaf
        node_tree_utils_get_node_name_488["27: get_node_name()"]:::leaf
    end

    %% Edges
    node___main___global_986 --> node___main___main_f54
    node___main___get_tree_parser_orchestrator_1d0 --> node_TreeOrchestrator___init___d80
    node___main___main_f54 --> node___main___merge_nix_trees_c57
    node___main___merge_nix_trees_c57 --> node___main___get_tree_parser_orchestrator_1d0
    node_app_global_897 --> node_app_main_9c5
    node_app_global_897 --> node_DatabaseStorage___init___8bc
    node_app_main_9c5 --> node_database_init_db_6e2
    node_app_run_scan_0f4 --> node_ScanPipeline_run_scan_d6e
    node_app_scan_endpoint_42a --> node_app_run_scan_0f4
    node_app_tree_endpoint_060 --> node_database_get_dependency_tree_for_scan_426
    node_app_tree_endpoint_060 --> node_database_init_db_6e2
    node_app_vulnerabilities_endpoint_aa6 --> node_database_get_vulnerabilities_since_ea4
    node_app_vulnerabilities_endpoint_aa6 --> node_database_init_db_6e2
    node_TreeFormatterImpl__format_children_32b --> node_TreeFormatterImpl__format_children_32b
    node_TreeFormatterImpl__format_children_top_level_558 --> node_TreeFormatterImpl__format_children_32b
    node_TreeFormatterImpl_generate_ascii_tree_d79 --> node_TreeFormatterImpl__format_children_32b
    node_TreeFormatterImpl_generate_ascii_tree_d79 --> node_TreeFormatterImpl__format_children_top_level_558
    node_merger__dict_to_text_5ab --> node_merger__dict_to_text_5ab
    node_merger__parse_display_name_ff8 --> node_merger__strip_tree_chars_2ad
    node_merger__parse_display_name_ff8 --> node_merger__strip_tree_chars_2ad
    node_merger__tree_to_dict_200 --> node_merger__parse_display_name_ff8
    node_merger__tree_to_dict_200 --> node_merger__tree_to_dict_200
    node_merger__trees_to_text_bca --> node_merger__dict_to_text_5ab
    node_TreeNormalizerImpl_normalize_d22 --> node_normalizer__traverse_tree_537
    node_normalizer__traverse_tree_537 --> node_normalizer__severity_from_cvss_86f
    node_normalizer__traverse_tree_537 --> node_normalizer__traverse_tree_537
    node_TreeParserImpl_parse_tree_block_b90 --> node_tree_utils_count_indent_2c7
    node_TreeParserImpl_parse_tree_block_b90 --> node_tree_utils_get_node_name_488
    node_MockStorage_insert_dependency_node_000 --> node_MockStorage__next_id_31b
    node_MockStorage_insert_scan_69c --> node_MockStorage__next_id_31b
    node_MockStorage_insert_vulnerability_event_e4d --> node_MockStorage__next_id_31b
    node_ScanPipeline__store_tree_nodes_e80 --> node_ScanPipeline__store_tree_nodes_e80
    node_ScanPipeline_default_ef1 --> node_TreeOrchestrator___init___d80
    node_ScanPipeline_default_ef1 --> node_MockStorage___init___3fb
    node_ScanPipeline_run_scan_d6e --> node_ScanPipeline__store_tree_nodes_e80
    node_TestFormatter_test_formatter_deep_tree_08b --> node_TreeFormatterImpl_generate_ascii_tree_d79
    node_TestFormatter_test_formatter_simple_tree_acd --> node_TreeFormatterImpl_generate_ascii_tree_d79
    node_TestMerger_test_merger_empty_trees_b5b --> node_TreeMergerImpl_merge_trees_40c
    node_TestMerger_test_merger_multiple_trees_overlap_48e --> node_TreeMergerImpl_merge_trees_40c
    node_TestMerger_test_merger_single_tree_7d9 --> node_TreeMergerImpl_merge_trees_40c
    node_TestOrchestrator_test_orchestrator_e63 --> node_TreeOrchestrator___init___d80
    node_TestOrchestrator_test_recursive_merge_718 --> node_TreeOrchestrator___init___d80
    node_TestParser_test_complex_tree_164 --> node_TreeParserImpl_parse_tree_block_b90
    node_TestParser_test_parse_tree_block_487 --> node_TreeParserImpl_parse_tree_block_b90
    node_TestParser_test_parser_split_logic_294 --> node_TreeParserImpl_split_into_trees_c6f
    node_TestDatabase_setUp_f4a --> node_database_init_db_6e2
    node_TestDatabase_test_get_dependency_tree_for_scan_5e9 --> node_database_get_dependency_tree_for_scan_426
    node_TestDatabase_test_get_dependency_tree_for_scan_5e9 --> node_database_insert_dependency_node_4a2
    node_TestDatabase_test_get_dependency_tree_for_scan_5e9 --> node_database_insert_scan_500
    node_TestDatabase_test_get_vulnerabilities_since_filters_outside_range_784 --> node_database_get_vulnerabilities_since_ea4
    node_TestDatabase_test_get_vulnerabilities_since_filters_outside_range_784 --> node_database_insert_scan_500
    node_TestDatabase_test_get_vulnerabilities_since_filters_outside_range_784 --> node_database_insert_vulnerability_event_09d
    node_TestDatabase_test_get_vulnerabilities_since_returns_events_d33 --> node_database_get_vulnerabilities_since_ea4
    node_TestDatabase_test_get_vulnerabilities_since_returns_events_d33 --> node_database_insert_scan_500
    node_TestDatabase_test_get_vulnerabilities_since_returns_events_d33 --> node_database_insert_vulnerability_event_09d
    node_TestDatabase_test_get_vulnerabilities_since_with_until_171 --> node_database_get_vulnerabilities_since_ea4
    node_TestDatabase_test_get_vulnerabilities_since_with_until_171 --> node_database_insert_scan_500
    node_TestDatabase_test_get_vulnerabilities_since_with_until_171 --> node_database_insert_vulnerability_event_09d
    node_TestDatabase_test_insert_dependency_node_returns_id_5d4 --> node_database_insert_dependency_node_4a2
    node_TestDatabase_test_insert_dependency_node_returns_id_5d4 --> node_database_insert_scan_500
    node_TestDatabase_test_insert_scan_returns_id_f78 --> node_database_insert_scan_500
    node_TestDatabase_test_insert_vulnerability_event_returns_id_5bd --> node_database_insert_scan_500
    node_TestDatabase_test_insert_vulnerability_event_returns_id_5bd --> node_database_insert_vulnerability_event_09d
    node_TestDictToText_test_node_with_children_926 --> node_merger__dict_to_text_5ab
    node_TestDictToText_test_simple_node_157 --> node_merger__dict_to_text_5ab
    node_TestTreesToText_test_empty_list_9b0 --> node_merger__trees_to_text_bca
    node_TestTreesToText_test_multiple_trees_1ef --> node_merger__trees_to_text_bca
    node_TestTreesToText_test_single_tree_9d9 --> node_merger__trees_to_text_bca
    node_TestNormalizeTree_setUp_89e --> node_test_normalizer__make_vuln_lookup_9a5
    node_TestSeverityFromCvss_test_critical_score_9e1 --> node_normalizer__severity_from_cvss_86f
    node_TestSeverityFromCvss_test_critical_score_9e1 --> node_normalizer__severity_from_cvss_86f
    node_TestSeverityFromCvss_test_critical_score_9e1 --> node_normalizer__severity_from_cvss_86f
    node_TestSeverityFromCvss_test_high_score_47d --> node_normalizer__severity_from_cvss_86f
    node_TestSeverityFromCvss_test_high_score_47d --> node_normalizer__severity_from_cvss_86f
    node_TestSeverityFromCvss_test_high_score_47d --> node_normalizer__severity_from_cvss_86f
    node_TestSeverityFromCvss_test_low_score_43e --> node_normalizer__severity_from_cvss_86f
    node_TestSeverityFromCvss_test_low_score_43e --> node_normalizer__severity_from_cvss_86f
    node_TestSeverityFromCvss_test_medium_score_8b4 --> node_normalizer__severity_from_cvss_86f
    node_TestSeverityFromCvss_test_medium_score_8b4 --> node_normalizer__severity_from_cvss_86f
    node_TestSeverityFromCvss_test_medium_score_8b4 --> node_normalizer__severity_from_cvss_86f
    node_TestMockDependencyMapper_test_why_depends_returns_trees_73d --> node_MockDependencyMapper_why_depends_ea8
    node_TestMockDerivationSource_test_show_derivation_returns_dict_93f --> node_MockDerivationSource_show_derivation_529
    node_TestMockStorage_test_insert_dependency_node_74d --> node_MockStorage___init___3fb
    node_TestMockStorage_test_insert_dependency_node_74d --> node_MockStorage_insert_dependency_node_000
    node_TestMockStorage_test_insert_dependency_node_74d --> node_MockStorage_insert_scan_69c
    node_TestMockStorage_test_insert_dependency_node_74d --> node_MockStorage_insert_vulnerability_event_e4d
    node_TestMockStorage_test_insert_dependency_node_74d --> node_MockStorage_insert_vulnerability_event_e4d
    node_TestMockStorage_test_insert_scan_b7a --> node_MockStorage___init___3fb
    node_TestMockStorage_test_insert_scan_b7a --> node_MockStorage_insert_scan_69c
    node_TestMockStorage_test_insert_scan_b7a --> node_MockStorage_insert_scan_69c
    node_TestMockStorage_test_insert_vulnerability_event_874 --> node_MockStorage___init___3fb
    node_TestMockStorage_test_insert_vulnerability_event_874 --> node_MockStorage_insert_scan_69c
    node_TestMockStorage_test_insert_vulnerability_event_874 --> node_MockStorage_insert_vulnerability_event_e4d
    node_TestMockStorage_test_insert_vulnerability_event_874 --> node_MockStorage_insert_vulnerability_event_e4d
    node_TestMockVulnerabilityScanner_test_scan_returns_vulnerabilities_b1f --> node_MockVulnerabilityScanner_scan_vulnerabilities_10c
    node_TestScanPipelineWithCustomStages_test_run_scan_with_custom_stages_7f0 --> node_MockStorage__next_id_31b
    node_TestScanPipelineWithCustomStages_test_run_scan_with_custom_stages_7f0 --> node_MockStorage__next_id_31b
    node_TestScanPipelineWithCustomStages_test_run_scan_with_custom_stages_7f0 --> node_MockStorage__next_id_31b
    node_TestScanPipelineWithCustomStages_test_run_scan_with_custom_stages_7f0 --> node_ScanPipeline___init___136
    node_TestScanPipelineWithCustomStages_test_run_scan_with_custom_stages_7f0 --> node_ScanPipeline_run_scan_d6e
    node_TestTreeMergerImpl_test_merge_empty_returns_empty_481 --> node_TreeMergerImpl_merge_trees_40c
    node_TestTreeMergerImpl_test_merge_single_tree_047 --> node_TreeMergerImpl_merge_trees_40c
    node_TestTreeNormalizerImpl_test_normalize_empty_tree_115 --> node_TreeNormalizerImpl_normalize_d22
    node_TestTreeNormalizerImpl_test_normalize_with_custom_lookup_847 --> node_TreeNormalizerImpl_normalize_d22
    node_TestTreeNormalizerImpl_test_normalize_with_mock_lookup_9f8 --> node_TreeNormalizerImpl_normalize_d22
    node_TestTreeNormalizerImpl_test_normalize_with_mock_lookup_9f8 --> node_TestTreeNormalizerImpl__make_vuln_map_246

    %% Edge styles
    linkStyle 0 stroke:#D55E00
    linkStyle 1 stroke:#000000
    linkStyle 2 stroke:#F0E442
    linkStyle 3 stroke:#CC79A7
    linkStyle 4 stroke:#CC79A7
    linkStyle 5 stroke:#CC79A7
    linkStyle 6 stroke:#0072B2
    linkStyle 7 stroke:#F0E442
    linkStyle 8 stroke:#56B4E9
    linkStyle 9 stroke:#000000
    linkStyle 10 stroke:#000000
    linkStyle 11 stroke:#D55E00
    linkStyle 12 stroke:#D55E00
    linkStyle 13 stroke:#009E73
    linkStyle 14 stroke:#000000
    linkStyle 15 stroke:#E69F00
    linkStyle 16 stroke:#E69F00
    linkStyle 17 stroke:#009E73
    linkStyle 18 stroke:#000000
    linkStyle 19 stroke:#000000
    linkStyle 20 stroke:#000000
    linkStyle 21 stroke:#000000
    linkStyle 22 stroke:#56B4E9
    linkStyle 23 stroke:#56B4E9
    linkStyle 24 stroke:#CC79A7
    linkStyle 25 stroke:#CC79A7
    linkStyle 26 stroke:#000000
    linkStyle 27 stroke:#000000
    linkStyle 28 stroke:#000000
    linkStyle 29 stroke:#F0E442
    linkStyle 30 stroke:#0072B2
    linkStyle 31 stroke:#000000
    linkStyle 32 stroke:#E69F00
    linkStyle 33 stroke:#E69F00
    linkStyle 34 stroke:#D55E00
    linkStyle 35 stroke:#009E73
    linkStyle 36 stroke:#0072B2
    linkStyle 37 stroke:#009E73
    linkStyle 38 stroke:#D55E00
    linkStyle 39 stroke:#E69F00
    linkStyle 40 stroke:#009E73
    linkStyle 41 stroke:#000000
    linkStyle 42 stroke:#F0E442
    linkStyle 43 stroke:#CC79A7
    linkStyle 44 stroke:#F0E442
    linkStyle 45 stroke:#56B4E9
    linkStyle 46 stroke:#E69F00
    linkStyle 47 stroke:#E69F00
    linkStyle 48 stroke:#E69F00
    linkStyle 49 stroke:#F0E442
    linkStyle 50 stroke:#F0E442
    linkStyle 51 stroke:#F0E442
    linkStyle 52 stroke:#009E73
    linkStyle 53 stroke:#009E73
    linkStyle 54 stroke:#009E73
    linkStyle 55 stroke:#E69F00
    linkStyle 56 stroke:#E69F00
    linkStyle 57 stroke:#E69F00
    linkStyle 58 stroke:#F0E442
    linkStyle 59 stroke:#F0E442
    linkStyle 60 stroke:#000000
    linkStyle 61 stroke:#0072B2
    linkStyle 62 stroke:#0072B2
    linkStyle 63 stroke:#D55E00
    linkStyle 64 stroke:#CC79A7
    linkStyle 65 stroke:#000000
    linkStyle 66 stroke:#CC79A7
    linkStyle 67 stroke:#E69F00
    linkStyle 68 stroke:#D55E00
    linkStyle 69 stroke:#E69F00
    linkStyle 70 stroke:#E69F00
    linkStyle 71 stroke:#E69F00
    linkStyle 72 stroke:#0072B2
    linkStyle 73 stroke:#0072B2
    linkStyle 74 stroke:#0072B2
    linkStyle 75 stroke:#D55E00
    linkStyle 76 stroke:#D55E00
    linkStyle 77 stroke:#F0E442
    linkStyle 78 stroke:#F0E442
    linkStyle 79 stroke:#F0E442
    linkStyle 80 stroke:#0072B2
    linkStyle 81 stroke:#CC79A7
    linkStyle 82 stroke:#0072B2
    linkStyle 83 stroke:#0072B2
    linkStyle 84 stroke:#0072B2
    linkStyle 85 stroke:#0072B2
    linkStyle 86 stroke:#0072B2
    linkStyle 87 stroke:#56B4E9
    linkStyle 88 stroke:#56B4E9
    linkStyle 89 stroke:#56B4E9
    linkStyle 90 stroke:#F0E442
    linkStyle 91 stroke:#F0E442
    linkStyle 92 stroke:#F0E442
    linkStyle 93 stroke:#F0E442
    linkStyle 94 stroke:#CC79A7
    linkStyle 95 stroke:#000000
    linkStyle 96 stroke:#000000
    linkStyle 97 stroke:#000000
    linkStyle 98 stroke:#000000
    linkStyle 99 stroke:#000000
    linkStyle 100 stroke:#E69F00
    linkStyle 101 stroke:#CC79A7
    linkStyle 102 stroke:#0072B2
    linkStyle 103 stroke:#CC79A7
    linkStyle 104 stroke:#000000
    linkStyle 105 stroke:#000000

    %% Node styles
    classDef filled fill:#555555,stroke:#000000,stroke-width:2px;
    classDef leaf fill:#5555FF,stroke:#000000,stroke-width:2px;
    classDef trunk fill:#AA5555,stroke:#000000,stroke-width:2px;
```