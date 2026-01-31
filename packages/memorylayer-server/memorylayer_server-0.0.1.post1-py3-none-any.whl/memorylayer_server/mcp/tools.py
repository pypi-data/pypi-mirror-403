"""MCP tool definitions for MemoryLayer.ai."""

# Core tools (6) - always available
CORE_TOOLS = [
    {
        "name": "memory_remember",
        "description": "Store a new memory for later recall. Use for facts, preferences, decisions, or events worth remembering.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "The memory content to store"
                },
                "type": {
                    "type": "string",
                    "enum": ["episodic", "semantic", "procedural", "working"],
                    "description": "Memory type: episodic (events), semantic (facts), procedural (how-to), working (current context)"
                },
                "importance": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1,
                    "description": "How important (0-1). Higher values = retained longer and ranked higher in recall"
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Tags for categorization (e.g., ['python', 'bug-fix'])"
                },
                "subtype": {
                    "type": "string",
                    "enum": ["Solution", "Problem", "CodePattern", "Fix", "Error", "Workflow", "Preference", "Decision"],
                    "description": "Optional domain-specific classification"
                }
            },
            "required": ["content"]
        }
    },
    {
        "name": "memory_recall",
        "description": "Search memories by semantic query. Returns relevant memories ranked by relevance. Use this to find previously stored information.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language query (e.g., 'How do I fix authentication errors?')"
                },
                "types": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["episodic", "semantic", "procedural", "working"]
                    },
                    "description": "Filter by memory types"
                },
                "limit": {
                    "type": "integer",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 100,
                    "description": "Max memories to return"
                },
                "min_relevance": {
                    "type": "number",
                    "default": 0.5,
                    "minimum": 0,
                    "maximum": 1,
                    "description": "Min relevance score (0-1)"
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Filter by tags (AND logic)"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "memory_reflect",
        "description": "Synthesize and summarize memories matching a query. Use when you need insights across multiple memories rather than individual recall results.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "What to reflect on (e.g., 'What patterns have we seen with database performance?')"
                },
                "max_tokens": {
                    "type": "integer",
                    "default": 500,
                    "minimum": 50,
                    "maximum": 4000,
                    "description": "Max tokens in reflection"
                },
                "include_sources": {
                    "type": "boolean",
                    "default": True,
                    "description": "Include source memory IDs in response"
                },
                "depth": {
                    "type": "integer",
                    "default": 2,
                    "minimum": 1,
                    "maximum": 5,
                    "description": "Association traversal depth (how many hops to follow)"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "memory_forget",
        "description": "Delete or decay a memory when information is outdated or incorrect. Use sparingly - memories are useful historical context.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "memory_id": {
                    "type": "string",
                    "description": "ID of memory to forget"
                },
                "reason": {
                    "type": "string",
                    "description": "Why this memory should be forgotten (for audit trail)"
                },
                "hard": {
                    "type": "boolean",
                    "default": False,
                    "description": "Hard delete (permanent) vs soft delete (recoverable)"
                }
            },
            "required": ["memory_id"]
        }
    },
    {
        "name": "memory_associate",
        "description": "Link two memories with a relationship. Helps build knowledge graph for traversal and causal reasoning.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "source_id": {
                    "type": "string",
                    "description": "Source memory ID"
                },
                "target_id": {
                    "type": "string",
                    "description": "Target memory ID"
                },
                "relationship": {
                    "type": "string",
                    "enum": [
                        "CAUSES", "TRIGGERS", "LEADS_TO", "PREVENTS", "SOLVES", "ADDRESSES",
                        "ALTERNATIVE_TO", "IMPROVES", "OCCURS_IN", "APPLIES_TO", "WORKS_WITH",
                        "REQUIRES", "BUILDS_ON", "CONTRADICTS", "CONFIRMS", "SUPERSEDES",
                        "SIMILAR_TO", "VARIANT_OF", "RELATED_TO", "FOLLOWS", "DEPENDS_ON",
                        "ENABLES", "BLOCKS", "EFFECTIVE_FOR", "PREFERRED_OVER", "DEPRECATED_BY"
                    ],
                    "description": "Type of relationship between memories"
                },
                "strength": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1,
                    "default": 0.8,
                    "description": "Strength of association (0-1)"
                }
            },
            "required": ["source_id", "target_id", "relationship"]
        }
    },
    {
        "name": "memory_briefing",
        "description": "Get a session briefing summarizing recent activity and context. Use at session start to get oriented.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "lookback_hours": {
                    "type": "integer",
                    "default": 24,
                    "minimum": 1,
                    "maximum": 168,
                    "description": "How far back to look (in hours)"
                },
                "include_contradictions": {
                    "type": "boolean",
                    "default": True,
                    "description": "Flag contradicting memories in briefing"
                }
            }
        }
    }
]

# Extended tools (4) - optional advanced features
EXTENDED_TOOLS = [
    {
        "name": "memory_statistics",
        "description": "Get memory statistics and analytics for the workspace. Use to understand memory usage patterns.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "include_breakdown": {
                    "type": "boolean",
                    "default": True,
                    "description": "Include breakdown by type/subtype"
                }
            }
        }
    },
    {
        "name": "memory_graph_query",
        "description": "Multi-hop graph traversal to find related memories. Use to discover causal chains or knowledge paths.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "start_memory_id": {
                    "type": "string",
                    "description": "Starting memory ID"
                },
                "relationship_types": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Filter by relationship types (e.g., ['CAUSES', 'TRIGGERS'])"
                },
                "max_depth": {
                    "type": "integer",
                    "default": 3,
                    "minimum": 1,
                    "maximum": 5,
                    "description": "Maximum traversal depth"
                },
                "direction": {
                    "type": "string",
                    "enum": ["outgoing", "incoming", "both"],
                    "default": "both",
                    "description": "Traversal direction"
                },
                "max_paths": {
                    "type": "integer",
                    "default": 50,
                    "description": "Maximum paths to return"
                }
            },
            "required": ["start_memory_id"]
        }
    },
    {
        "name": "memory_audit",
        "description": "Audit memories for contradictions and inconsistencies. Use to maintain knowledge base health.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "memory_id": {
                    "type": "string",
                    "description": "Specific memory to audit (omit to audit entire workspace)"
                },
                "auto_resolve": {
                    "type": "boolean",
                    "default": False,
                    "description": "Automatically mark newer contradicting memories as preferred"
                }
            }
        }
    },
    {
        "name": "memory_compress",
        "description": "Compress or archive old memories to free up resources. Groups similar old memories into consolidated summaries.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "older_than_days": {
                    "type": "integer",
                    "default": 90,
                    "minimum": 30,
                    "description": "Compress memories older than this many days"
                },
                "min_access_count": {
                    "type": "integer",
                    "default": 0,
                    "description": "Only compress memories accessed fewer than this many times"
                },
                "preserve_important": {
                    "type": "boolean",
                    "default": True,
                    "description": "Preserve high-importance memories (importance > 0.7)"
                },
                "dry_run": {
                    "type": "boolean",
                    "default": True,
                    "description": "Preview what would be compressed without actually doing it"
                }
            }
        }
    }
]
