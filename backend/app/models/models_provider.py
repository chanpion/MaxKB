"""Model provider table alias.

The real table is ``model`` (defined once in :mod:`app.models.model`); there is
NO separate credential/provider table — provider metadata and encrypted
credentials live as JSON/CHAR columns on that single ``model`` table. This
module re-exports the canonical ``Model`` so the ``models_provider`` and
``local_model`` layers share the exact same table registration (avoiding a
duplicate ``__tablename__ == "model"`` conflict on ``SQLModel.metadata``).
"""

from app.models.model import Model

__all__ = ["Model"]
