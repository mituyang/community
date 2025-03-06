CREATE TABLE user (
	id INTEGER PRIMARY KEY AUTOINCREMENT, 
	username VARCHAR(80) NOT NULL, 
	password VARCHAR(120) NOT NULL, 
	email VARCHAR(120), 
	nickname VARCHAR(80), 
	avatar VARCHAR(255), 
	gender VARCHAR(6), 
	birthday DATE, 
	location VARCHAR(100), 
	website VARCHAR(255), 
	bio TEXT, 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	UNIQUE (username), 
	UNIQUE (email)
);
CREATE TABLE post (
	id INTEGER NOT NULL, 
	title VARCHAR(100) NOT NULL, 
	content TEXT NOT NULL, 
	user_id INTEGER NOT NULL, 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES user (id)
);
CREATE TABLE follows (
	id INTEGER NOT NULL, 
	follower_id INTEGER NOT NULL, 
	following_id INTEGER NOT NULL, 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	CONSTRAINT unique_follow UNIQUE (follower_id, following_id), 
	FOREIGN KEY(follower_id) REFERENCES user (id), 
	FOREIGN KEY(following_id) REFERENCES user (id)
);
CREATE TABLE post_view (
	id INTEGER NOT NULL, 
	post_id INTEGER NOT NULL, 
	author_id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	view_count INTEGER, 
	last_viewed_at DATETIME, 
	PRIMARY KEY (id), 
	UNIQUE (post_id), 
	FOREIGN KEY(post_id) REFERENCES post (id), 
	FOREIGN KEY(author_id) REFERENCES user (id), 
	FOREIGN KEY(user_id) REFERENCES user (id)
);
CREATE TABLE post_like (
	id INTEGER NOT NULL, 
	post_id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	CONSTRAINT unique_post_user_like UNIQUE (post_id, user_id), 
	FOREIGN KEY(post_id) REFERENCES post (id), 
	FOREIGN KEY(user_id) REFERENCES user (id)
);
CREATE TABLE post_comment (
	id INTEGER NOT NULL, 
	post_id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	content TEXT NOT NULL, 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(post_id) REFERENCES post (id), 
	FOREIGN KEY(user_id) REFERENCES user (id)
);
CREATE TABLE post_share (
	id INTEGER NOT NULL, 
	post_id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(post_id) REFERENCES post (id), 
	FOREIGN KEY(user_id) REFERENCES user (id)
);

CREATE TABLE comment_like (
	id INTEGER NOT NULL, 
	comment_id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	CONSTRAINT uk_comment_like UNIQUE (comment_id, user_id), 
	FOREIGN KEY(comment_id) REFERENCES post_comment (id) ON DELETE CASCADE, 
	FOREIGN KEY(user_id) REFERENCES user (id) ON DELETE CASCADE
);
CREATE TABLE comment_share (
	id INTEGER NOT NULL, 
	comment_id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	CONSTRAINT uk_comment_share UNIQUE (comment_id, user_id), 
	FOREIGN KEY(comment_id) REFERENCES post_comment (id) ON DELETE CASCADE, 
	FOREIGN KEY(user_id) REFERENCES user (id) ON DELETE CASCADE
);
CREATE TABLE comment_reply (
	id INTEGER NOT NULL, 
	parent_comment_id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	content TEXT NOT NULL, 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(parent_comment_id) REFERENCES post_comment (id) ON DELETE CASCADE, 
	FOREIGN KEY(user_id) REFERENCES user (id) ON DELETE CASCADE
);
CREATE TABLE notifications (
	id INTEGER NOT NULL, 
	recipient_id INTEGER NOT NULL, 
	sender_id INTEGER NOT NULL, 
	type VARCHAR(20) NOT NULL, 
	post_id INTEGER, 
	comment_id INTEGER, 
	content TEXT, 
	is_read BOOLEAN, 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	CONSTRAINT check_no_self_notification CHECK (recipient_id <> sender_id), 
	FOREIGN KEY(recipient_id) REFERENCES user (id), 
	FOREIGN KEY(sender_id) REFERENCES user (id), 
	FOREIGN KEY(post_id) REFERENCES post (id), 
	FOREIGN KEY(comment_id) REFERENCES post_comment (id)
);


