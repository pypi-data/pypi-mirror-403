# Open-WebUI Internal SQLite Database

For Open-WebUI, the SQLite database serves as the backbone for user management, chat history, file storage, and various other core functionalities. Understanding this structure is essential for anyone looking to contribute to or maintain the project effectively.
Internal SQLite Location

You can find the SQLite database at root -> data -> webui.db

📁 Root (/)
├── 📁 data
│   ├── 📁 cache
│   ├── 📁 uploads
│   ├── 📁 vector_db
│   └── 📄 webui.db
├── 📄 dev.sh
├── 📁 open_webui
├── 📄 requirements.txt
├── 📄 start.sh
└── 📄 start_windows.bat

# Table Overview

Here is a complete list of tables in Open-WebUI's SQLite database. The tables are listed alphabetically and numbered for convenience.
This document only holds the tables taht are relevant for this project.

No.	Table Name	Description
01	auth	Stores user authentication credentials and login information
02	channel	Manages chat channels and their configurations
03	channel_file	Links files to channels and messages
04	channel_member	Tracks user membership and permissions within channels
05	chat	Stores chat sessions and their metadata
06	chat_file	Links files to chats and messages
07	chatidtag	Maps relationships between chats and their associated tags
08	config	Maintains system-wide configuration settings
09	document	Stores documents and their metadata for knowledge management
10	feedback	Captures user feedback and ratings
11	file	Manages uploaded files and their metadata
12	folder	Organizes files and content into hierarchical structures
13	function	Stores custom functions and their configurations
14	group	Manages user groups and their permissions
15	group_member	Tracks user membership within groups
16	knowledge	Stores knowledge base entries and related information
17	knowledge_file	Links files to knowledge bases
18	memory	Maintains chat history and context memory
19	message	Stores individual chat messages and their content
20	message_reaction	Records user reactions (emojis/responses) to messages
21	migrate_history	Tracks database schema version and migration records
22	model	Manages AI model configurations and settings
23	note	Stores user-created notes and annotations
24	oauth_session	Manages active OAuth sessions for users
25	prompt	Stores templates and configurations for AI prompts
26	tag	Manages tags/labels for content categorization
27	tool	Stores configurations for system tools and integrations
28	user	Maintains user profiles and account information

Note: there are two additional tables in Open-WebUI's SQLite database that are not related to Open-WebUI's core functionality, that have been excluded:

    Alembic Version table
    Migrate History table

Now that we have all the tables, let's understand the structure of each table.
Auth Table
Column Name	Data Type	Constraints	Description
id	String	PRIMARY KEY	Unique identifier
email	String	-	User's email
password	Text	-	Hashed password
active	Boolean	-	Account status

Things to know about the auth table:

    Uses UUID for primary key
    One-to-One relationship with users table (shared id)


# Group Table

Column Name	Data Type	Constraints	Description
id	Text	PRIMARY KEY, UNIQUE	Unique identifier (UUID)
user_id	Text	-	Group owner/creator
name	Text	-	Group name
description	Text	-	Group description
data	JSON	nullable	Additional group data
meta	JSON	nullable	Group metadata
permissions	JSON	nullable	Permission configuration
created_at	BigInteger	-	Creation timestamp
updated_at	BigInteger	-	Last update timestamp

Note: The user_ids column has been migrated to the group_member table.

# Group Member Table

Column Name	Data Type	Constraints	Description
id	Text	PRIMARY KEY, UNIQUE	Unique identifier (UUID)
group_id	Text	FOREIGN KEY(group.id), NOT NULL	Reference to the group
user_id	Text	FOREIGN KEY(user.id), NOT NULL	Reference to the user
created_at	BigInteger	nullable	Creation timestamp
updated_at	BigInteger	nullable	Last update timestamp

Things to know about the group_member table:

    Unique constraint on (group_id, user_id) to prevent duplicate memberships
    Foreign key relationships with CASCADE delete to group and user tables

# Model Table

Column Name	Data Type	Constraints	Description
id	Text	PRIMARY KEY	Model identifier
user_id	Text	-	Model owner
base_model_id	Text	nullable	Parent model reference
name	Text	-	Display name
params	JSON	-	Model parameters
meta	JSON	-	Model metadata
access_control	JSON	nullable	Access permissions
is_active	Boolean	default=True	Active status
created_at	BigInteger	-	Creation timestamp
updated_at	BigInteger	-	Last update timestamp

# Prompt Table

Column Name	Data Type	Constraints	Description
command	String	PRIMARY KEY	Unique command identifier
user_id	String	-	Prompt owner
title	Text	-	Prompt title
content	Text	-	Prompt content/template
timestamp	BigInteger	-	Last update timestamp
access_control	JSON	nullable	Access permissions
Tag Table
Column Name	Data Type	Constraints	Description
id	String	PK (composite)	Normalized tag identifier
name	String	-	Display name
user_id	String	PK (composite)	Tag owner
meta	JSON	nullable	Tag metadata

Things to know about the tag table:

    Primary key is composite (id, user_id)

# Tool Table

Column Name	Data Type	Constraints	Description
id	String	PRIMARY KEY	Unique identifier
user_id	String	-	Tool owner
name	Text	-	Tool name
content	Text	-	Tool content/code
specs	JSON	-	Tool specifications
meta	JSON	-	Tool metadata
valves	JSON	-	Tool control settings
access_control	JSON	nullable	Access permissions
created_at	BigInteger	-	Creation timestamp
updated_at	BigInteger	-	Last update timestamp

# User Table

Column Name	Data Type	Constraints	Description
id	String	PRIMARY KEY	Unique identifier
username	String(50)	nullable	User's unique username
name	String	-	User's name
email	String	-	User's email
role	String	-	User's role
profile_image_url	Text	-	Profile image path
bio	Text	nullable	User's biography
gender	Text	nullable	User's gender
date_of_birth	Date	nullable	User's date of birth
last_active_at	BigInteger	-	Last activity timestamp
updated_at	BigInteger	-	Last update timestamp
created_at	BigInteger	-	Creation timestamp
api_key	String	UNIQUE, nullable	API authentication key
settings	JSON	nullable	User preferences
info	JSON	nullable	Additional user info
oauth_sub	Text	UNIQUE	OAuth subject identifier