-- Sample Data for Item Finder System

-- 1. Users
INSERT INTO `user` (`id`, `username`, `email`, `password`, `role`) VALUES
(1, 'admin', 'jasfer.ly1@gmail.com', 'scrypt:hashed...', 'admin'),
(2, 'Jasfer', 'sekwethuhu@gmail.com', 'scrypt:hashed...', 'user'),
(4, 'Bacon', 'latjasfermoto@gmail.com', 'pbkdf2:hashed...', 'user');

-- 2. Items
INSERT INTO `item` (`name`, `category`, `status`, `is_approved`, `item_location`, `user_id`) VALUES
('iphone 13 pro max', 'Electronics', 'Lost', 1, 'Library', 2),
('Diary', 'Other', 'Found', 0, 'BSULIPA HEB 502', 2),
('Jisulife Mini fan', 'Electronics', 'Lost', 1, 'Jollibee at SM LIPA', 4),
('Airpods pro 3rd gen', 'Electronics', 'Claimed', 1, 'BSULIPA LIBRARY', 2);

-- 3. Notifications
INSERT INTO `notification` (`user_id`, `message`, `is_read`, `timestamp`) VALUES
(1, 'New user registered: Jasfer (sekwethuhu@gmail.com)', 1, '2025-12-17 09:40:32'),
(2, 'Item \'iphone 13 pro max\' approved!', 1, '2025-12-17 10:54:57');