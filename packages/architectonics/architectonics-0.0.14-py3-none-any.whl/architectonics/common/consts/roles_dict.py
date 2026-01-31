from enum import Enum


class Roles(str, Enum):
    SUPER_ADMIN = "SuperAdmin"
    TEACHER = "Teacher"
    STUDENT = "Student"
