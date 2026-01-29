#!/usr/bin/env python3

# File: gntplib/notifier.py
# Author: Hadi Cahyadi <cumulus13@gmail.com>
# Date: 2026-01-03
# Description: 
# License: MIT

from .lib import Publisher, Resource

__all__ = ['GrowlNotifier', "Resource", "Publisher"]

class GrowlNotifier(Publisher):
	"""Alias for GrowlNotifier for backward compatibility."""
	pass