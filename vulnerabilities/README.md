# Tree Parser

A Python library for parsing and merging tree structures from Nix store listings.

## Architecture

The project uses an interface-driven architecture to ensure decoupling and testability.

```mermaid
graph TD
    subgraph interfaces
        TreeParser[TreeParser Interface]
        TreeMerger[TreeMergo Interface]
        TreeFormatter[TreeFormatter Interface]
        TreeOrchestrator[TreeOrchestrator Interface]
    end

    subgraph core
        TreeParserImpl[TreeParser Implementation]
        TreeMergerImpl[TreeMerger Implementation]
        TreeFormatterImpl[TreeFormatter Implementation]
        TreeOrchestratorImpl[TreeOrchestrator Implementation]
    end

    subgraph utils
        TreeUtils[Tree Utilities]
    end

    TreeParserImpl -.- TreeParser
    TreeMergerImpl -.- TreeMerger
    TreeFormatterImpl -.- TreeFormatter
    TreeOrchestratorImpl -.- TreeOrchestrator
    TreeParserImpl --> TreeUtils
    TreeMergerImpl --> TreeUtils
