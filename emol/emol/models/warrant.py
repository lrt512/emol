# -*- coding: utf-8 -*-
"""Combatant warrant model."""

# standard library imports

# third-party imports
from flask import current_app as app

# application imports
from .card import Card

__all__ = ['Warrant']


class Warrant(app.db.Model):
    """Link a marshallate to a combatant via the appropriate card.

    Properties:
        combatant: The combatant
        marshal: The marshallate office held

    """
    __tablename__ = 'warrant'
    __table_args__ = (app.db.UniqueConstraint('card_id', 'marshal_id'),)

    card_id = app.db.Column(
        app.db.Integer,
        app.db.ForeignKey('card.id'),
        primary_key=True
    )

    marshal_id = app.db.Column(
        app.db.Integer,
        app.db.ForeignKey('marshal.id'),
        primary_key=True
    )

    card = app.db.relationship('Card', uselist=False)
    marshal = app.db.relationship('Marshal', uselist=False)
    '''
    combatant = app.db.relationship(
        'Combatant',
        secondary=Card.__table__,
        primaryjoin='Warrant.card_id==Card.id',
        secondaryjoin='Combatant.id==Card.combatant_id',
        uselist=False
    )
    '''

    def __repr__(self):
        """String representation."""
        return '<Combatant Marshal: {0} => {1}.{2}'.format(
            self.card.combatant.email,
            self.marshal.discipline.slug,
            self.marshal.slug
        )

