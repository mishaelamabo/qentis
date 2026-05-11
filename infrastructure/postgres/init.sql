-- Create all 7 isolated databases on first start
CREATE DATABASE auth_db;
CREATE DATABASE institution_db;
CREATE DATABASE item_db;
CREATE DATABASE blockchain_db;
CREATE DATABASE output_db;
CREATE DATABASE verify_db;
CREATE DATABASE admin_db;

GRANT ALL PRIVILEGES ON DATABASE auth_db TO qentis_user;
GRANT ALL PRIVILEGES ON DATABASE institution_db TO qentis_user;
GRANT ALL PRIVILEGES ON DATABASE item_db TO qentis_user;
GRANT ALL PRIVILEGES ON DATABASE blockchain_db TO qentis_user;
GRANT ALL PRIVILEGES ON DATABASE output_db TO qentis_user;
GRANT ALL PRIVILEGES ON DATABASE verify_db TO qentis_user;
GRANT ALL PRIVILEGES ON DATABASE admin_db TO qentis_user;
