from dataclasses import dataclass


@dataclass(frozen=True)
class SuperAdminUser:
    id: str = "fb0c95e7-8608-4722-a7e4-04e11f9f1be8"
    first_name: str = "Super"
    last_name: str = "User"
