# Models: User & Team

## User Class
- **Path**: `app.models.User`
- **Inherits from**: `django.contrib.auth.models.AbstractUser`

### Overview
Extends the default Django User model to include role-based permissions and bio information.

### Key Attributes
- `role`: `CharField` with choices: `ORGANIZER`, `JURY`, `PARTICIPANT`.
- `bio`: `CharField` (max 200) for user self-description.
- `username`: `CharField` (max 20) unique identifier.

### Key Methods
- `is_organizer()`: Returns `True` if user has the Organizer role.
- `is_jury()`: Returns `True` if user has the Jury role.
- `is_participant()`: Returns `True` if user has the Participant role.

---

## Team Class
- **Path**: `app.models.Team`
- **Inherits from**: `django.db.models.Model`

### Overview
Represents a group of participants competing together in a contest.

### Key Attributes
- `name`: `CharField` (max 100) name of the team.
- `description`: `TextField` (max 200) about the team.
- `status`: `CharField` with choices: `DRAFT`, `ACTIVE`.
- `participants`: `ManyToManyField` to `User`.
- `captain`: `ForeignKey` to `User` (the team lead).
- `blacklisted_members`: `ManyToManyField` to `User`.
- `organization`: `CharField` (max 100) affiliated organization.

### Usage Example
```python
team = Team.objects.create(name="Alpha", captain=user)
team.participants.add(user)
```
