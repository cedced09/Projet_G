from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql+psycopg://gite_agent:gite_agent@localhost:5432/gite_agent"
    email_imap_host: str | None = None
    email_imap_port: int = 993
    email_imap_username: str | None = None
    email_imap_password: str | None = None
    email_imap_folder: str = "INBOX"
    email_imap_search: str = "UNSEEN"
    email_import_limit: int = 25
    email_max_listings_per_message: int = 5
    email_allowed_sender_domains: str = ""
    email_allowed_url_domains: str = ""
    html_auto_download_allowed_domains: str = ""
    html_import_directories: str = "./data/html-import,/html-import,~/Downloads"
