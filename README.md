```mermaid
erDiagram
    users {
        SERIAL id PK "Auto-incrementing ID"
        VARCHAR username "Username (unique)"
        CHAR password_hash "Password hash (bcrypt)"
        VARCHAR email "Email (unique)"
        VARCHAR avatar "Avatar URL"
        TEXT bio "Biography"
        ROLE role "User role (user, admin)"
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at
        TIMESTAMPTZ last_login
        VARCHAR github_id "GitHub ID"
        VARCHAR gitee_id "Gitee ID"
        BOOLEAN in_use "Is account active"
    }

    projects {
        SERIAL id PK "Auto-incrementing ID"
        VARCHAR name "Project name"
        VARCHAR brief "Brief description"
        TEXT description "Full description"
        VARCHAR repo_url "Repository URL (unique)"
        VARCHAR website_url "Project website URL"
        VARCHAR download_url "Download URL"
        INTEGER stars "Star count"
        INTEGER forks "Fork count"
        INTEGER watchers "Watcher count"
        INTEGER contributors "Contributor count"
        INTEGER issues "Issue count"
        VARCHAR license "License type"
        VARCHAR programming_language "Main programming language"
        TEXT code_example "Code example"
        TIMESTAMPTZ last_commit_at "Last commit timestamp"
        NUMERIC average_rating "Average rating score"
        INTEGER rating_count "Number of ratings"
        TIMESTAMPTZ repo_created_at "Repository creation timestamp"
        TIMESTAMPTZ last_sync_at "Last sync with repo timestamp"
        PLATFORM platform "Platform (Github, Gitee)"
        VARCHAR platform_id "Platform-specific ID"
        INTEGER submitter_id FK "User ID of submitter"
        BOOLEAN is_approved "Is project approved"
        TIMESTAMPTZ approval_date "Approval timestamp"
        INTEGER view_count "View count"
        BOOLEAN is_feature "Is featured project"
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at
    }

    tags {
        SERIAL id PK "Auto-incrementing ID"
        VARCHAR name "Tag name (unique)"
        VARCHAR category "Tag category"
        VARCHAR description "Tag description"
    }

    project_tags {
        SERIAL id PK "Auto-incrementing ID"
        INTEGER project_id FK "Project ID"
        INTEGER tag_id FK "Tag ID"
    }

    ratings {
        SERIAL id PK "Auto-incrementing ID"
        INTEGER project_id FK "Project ID"
        INTEGER user_id FK "User ID"
        REAL score "Rating score (0-10)"
        BOOLEAN is_used "Is rating considered in average"
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at
    }

    comments {
        SERIAL id PK "Auto-incrementing ID"
        INTEGER project_id FK "Project ID"
        INTEGER user_id FK "User ID"
        TEXT content "Comment content"
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at
        INTEGER parent_id FK "Parent comment ID (for replies)"
    }

    favorites {
        SERIAL id PK "Auto-incrementing ID"
        INTEGER project_id FK "Project ID"
        INTEGER user_id FK "User ID"
        TIMESTAMPTZ created_at
    }

    notifications {
        SERIAL id PK "Auto-incrementing ID"
        INTEGER user_id FK "User ID receiving notification"
        TEXT content "Notification content"
        BOOLEAN is_read "Is notification read"
        INTEGER related_project_id FK "Related project ID (optional)"
        INTEGER related_comment_id FK "Related comment ID (optional)"
        TIMESTAMPTZ created_at
    }

    oauth_accounts {
        SERIAL id PK "Auto-incrementing ID"
        INTEGER user_id FK "User ID"
        PLATFORM platform "OAuth platform (Github, Gitee)"
        VARCHAR access_token "Access token"
        TIMESTAMPTZ created_at
    }

    sync_logs {
        SERIAL id PK "Auto-incrementing ID"
        INTEGER project_id FK "Project ID"
        TIMESTAMPTZ create_at "Log creation timestamp"
        VARCHAR status "Sync status"
    }

    images {
        SERIAL id PK "Auto-incrementing ID"
        UUID uuid "Unique image identifier"
        INTEGER user_id FK "User ID of uploader"
        INTEGER project_id FK "Project ID image belongs to"
        VARCHAR original_name "Original file name"
        TIMESTAMPTZ created_at
    }

    users ||--o{ projects : "submits (submitter_id)"
    projects ||--|{ project_tags : "has"
    tags ||--|{ project_tags : "applied to"
    users ||--|{ ratings : "rates"
    projects ||--|{ ratings : "is rated by"
    users ||--o{ comments : "posts"
    projects ||--o{ comments : "has"
    comments }o--o{ comments : "is reply to (parent_id)"
    users ||--|{ favorites : "favorites"
    projects ||--|{ favorites : "is favorited by"
    users ||--o{ notifications : "receives"
    projects }o--o{ notifications : "related to (optional)"
    comments }o--o{ notifications : "related to (optional)"
    users ||--o{ oauth_accounts : "has"
    projects ||--o{ sync_logs : "has"
    users ||--o{ images : "uploads"
    projects ||--o{ images : "has"
```

```json
{
  "settings": {
    "analysis": {
      "analyzer": {
        "ik_max_pinyin": {
          "tokenizer": "ik_max_word",
          "filter": "my_pinyin"
        }
      },
      "filter": {
        "my_pinyin": {
          "type": "pinyin",
          "keep_full_pinyin": false,
          "keep_joined_full_pinyin": true,
          "keep_original": true,
          "limit_first_letter_length": 16,
          "remove_duplicated_term": true,
          "none_chinese_pinyin_tokenize": false
        }
      }
    }
  },
  "mappings": {
    "properties": {
      "name": {
        "type": "text",
        "analyzer": "ik_max_pinyin",
        "search_analyzer": "ik_smart",
        "fields": {
          "suggest": {
            "type": "completion",
            "analyzer": "keyword",
            "search_analyzer": "keyword"
          }
        }
      },
      "brief": {
        "type": "text",
        "analyzer": "ik_max_pinyin",
        "search_analyzer": "ik_smart",
      },
      "description": {
        "type": "text",
        "analyzer": "ik_max_pinyin",
        "search_analyzer": "ik_smart",
      },
      "programming_language": {
        "type": "keyword"
      },
      "license": {
        "type": "keyword"
      },
      "platform": {
        "type": "keyword"
      },
      "is_featured": {
        "type": "boolean"
      },
      "tags": {
        "type": "integer"
      }
    }
  }
}
```

```json
{
  "query": {
    "bool": {
      "filter": [
        {
          "terms_set": {
            "tags": {
              "terms": [
                1,
                2,
                3
              ],
              "minimum_should_match": 1
            }
          }
        }
      ],
      "must": [
        {
          "multi_match": {
            "query": "pt",
            "fields": [
              "name^5",
              "brief^3",
              "description^1"
            ]
          }
        }
      ]
    }
  },
  "from": 0,
  "size": 10,
  "_source": false
}
```