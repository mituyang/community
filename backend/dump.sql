PRAGMA foreign_keys=OFF;
CREATE TABLE user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,  
    username TEXT NOT NULL,              
    password TEXT NOT NULL,
    email TEXT,                           
    nickname TEXT,
    avatar TEXT,
    gender TEXT CHECK(gender IN ('male', 'female', 'other')), 
    birthday TEXT,                        
    location TEXT,
    website TEXT,
    bio TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
    UNIQUE (username),
    UNIQUE (email)
);
CREATE TABLE post (
    id INTEGER PRIMARY KEY AUTOINCREMENT,  
	title TEXT NOT NULL, 
	content TEXT NOT NULL, 
	user_id INTEGER NOT NULL, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
	FOREIGN KEY(user_id) REFERENCES user (id)
);
CREATE TABLE follows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,  
	follower_id INTEGER NOT NULL, 
	following_id INTEGER NOT NULL, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
	CONSTRAINT unique_follow UNIQUE (follower_id, following_id), 
	FOREIGN KEY(follower_id) REFERENCES user (id), 
	FOREIGN KEY(following_id) REFERENCES user (id)
);
CREATE TABLE post_view (
    id INTEGER PRIMARY KEY AUTOINCREMENT,  
	post_id INTEGER NOT NULL, 
	author_id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	view_count INTEGER, 
	last_viewed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
	UNIQUE (post_id), 
	FOREIGN KEY(post_id) REFERENCES post (id), 
	FOREIGN KEY(author_id) REFERENCES user (id), 
	FOREIGN KEY(user_id) REFERENCES user (id)
);
CREATE TABLE post_like (
    id INTEGER PRIMARY KEY AUTOINCREMENT,  
	post_id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
	CONSTRAINT unique_post_user_like UNIQUE (post_id, user_id), 
	FOREIGN KEY(post_id) REFERENCES post (id), 
	FOREIGN KEY(user_id) REFERENCES user (id)
);
CREATE TABLE post_comment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,  
	post_id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	content TEXT NOT NULL, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	FOREIGN KEY(post_id) REFERENCES post (id), 
	FOREIGN KEY(user_id) REFERENCES user (id)
);
CREATE TABLE post_share (
    id INTEGER PRIMARY KEY AUTOINCREMENT,  
	post_id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
	FOREIGN KEY(post_id) REFERENCES post (id), 
	FOREIGN KEY(user_id) REFERENCES user (id)
);

CREATE TABLE comment_like (
    id INTEGER PRIMARY KEY AUTOINCREMENT,  
	comment_id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	CONSTRAINT uk_comment_like UNIQUE (comment_id, user_id), 
	FOREIGN KEY(comment_id) REFERENCES post_comment (id) ON DELETE CASCADE, 
	FOREIGN KEY(user_id) REFERENCES user (id) ON DELETE CASCADE
);
CREATE TABLE comment_share (
    id INTEGER PRIMARY KEY AUTOINCREMENT,  
	comment_id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	CONSTRAINT uk_comment_share UNIQUE (comment_id, user_id),
	FOREIGN KEY(comment_id) REFERENCES post_comment (id) ON DELETE CASCADE,
	FOREIGN KEY(user_id) REFERENCES user (id) ON DELETE CASCADE
);
CREATE TABLE comment_reply (
    id INTEGER PRIMARY KEY AUTOINCREMENT,  
	parent_comment_id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	content TEXT NOT NULL, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
	FOREIGN KEY(parent_comment_id) REFERENCES post_comment (id) ON DELETE CASCADE, 
	FOREIGN KEY(user_id) REFERENCES user (id) ON DELETE CASCADE
);
CREATE TABLE notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,  
	recipient_id INTEGER NOT NULL, 
	sender_id INTEGER NOT NULL, 
	type TEXT CHECK(type IN ('like', 'comment', 'follow')), 
	post_id INTEGER, 
	comment_id INTEGER, 
	content TEXT, 
	is_read INTEGER CHECK(is_read IN (0, 1)), 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
	CONSTRAINT check_no_self_notification CHECK (recipient_id <> sender_id), 
	FOREIGN KEY(recipient_id) REFERENCES user (id), 
	FOREIGN KEY(sender_id) REFERENCES user (id), 
	FOREIGN KEY(post_id) REFERENCES post (id), 
	FOREIGN KEY(comment_id) REFERENCES post_comment (id)
);