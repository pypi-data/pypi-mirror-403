#!/usr/bin/env python3

# File: test/test.py
# Author: Hadi Cahyadi <cumulus13@gmail.com>
# Date: 2026-01-03
# Description: 
# License: MIT

import traceback

try:
	from .. gntplib import Publisher, Resource, GrowlNotifier
except:
	from gntplib import Publisher, Resource, GrowlNotifier
from pathlib3 import Path  # type: ignore
import os

print(f"{'='*(int(os.get_terminal_size()[0]/3))} TEST WITH DEFAULT ARGUMENTS [1] {'='*(int(os.get_terminal_size()[0]/3))}")  # type: ignore

try:
	growl = Publisher(  # type: ignore
	    name="Network Monitor",
	    event_defs=["Status Update"],
	    hostname='127.0.0.1',
	    port=23053
	)

	# Register application
	growl.register()

	# Read icon if exists
	icon = Path(__file__).parent / 'logo.png'
	print(f"ICON PATH: {icon}")
	print(f"ICON PATH is file: {Path(icon).is_file()}")

	# Send notification
	title = "TEST_TITLE"
	message = "TEST WITH DEFAULT ARGUMENTS [1]"
	priority = 0
	growl.publish(
	    name="Status Update",
	    title=title,
	    text=message,
	    icon=Resource(str(icon)) if Path(icon).exists() else None,  # type: ignore
	    sticky=False,
	    priority=priority
	)
	print(f"Sent notification with title: '{title}' and message: '{message}' successfully.")
	# print("="*(os.get_terminal_size()[0] - 11))
except Exception as e:
	print(f"ERROR DURING TEST: {e}")


print(f"{'='*(int(os.get_terminal_size()[0]/3))} TEST WITH ARGUMENTS ALIASES {'='*(int(os.get_terminal_size()[0]/3))}")  # type: ignore

try:
	growl = Publisher(  # type: ignore
	    applicationName="Network Monitor",
	    notifications=["Status Update"],
	    hostname='127.0.0.1',
	    port=23053
	)

	# Register application
	growl.register()

	# Read icon if exists
	icon = Path(__file__).parent / 'logo.png'
	print(f"ICON PATH: {icon}")
	print(f"ICON PATH is file: {Path(icon).is_file()}")

	# Send notification
	title = "TEST_TITLE"
	message = "TEST WITH ARGUMENTS ALIASES"
	priority = 0
	growl.publish(
	    noteType="Status Update",
	    title=title,
	    description=message,
	    icon=Resource(str(icon)) if Path(icon).exists() else None,  # type: ignore
	    sticky=False,
	    priority=priority
	)
	print(f"Sent notification with aliases and title: '{title}' and message: '{message}' successfully.")
	# print("="*(os.get_terminal_size()[0] - 11))
except Exception as e:
	print(f"ERROR DURING TEST: {e}")

print(f"{'='*(int(os.get_terminal_size()[0]/3))} TEST WITH DEFAULT ARGUMENTS [2] {'='*(int(os.get_terminal_size()[0]/3))}")  # type: ignore

try:
	growl = Publisher(  # type: ignore
	    "Network Monitor",
	    ["Status Update"],
	    hostname='127.0.0.1',
	    port=23053
	)

	# Register application
	growl.register()

	# Read icon if exists
	icon = Path(__file__).parent / 'logo.png'
	print(f"ICON PATH: {icon}")
	print(f"ICON PATH is file: {Path(icon).is_file()}")

	# Send notification
	title = "TEST_TITLE"
	message = "TEST WITH DEFAULT ARGUMENTS [2]"
	priority = 0
	growl.publish(
	    "Status Update",
	    title,
	    message,
	    icon=Resource(str(icon)) if Path(icon).exists() else None,  # type: ignore
	    sticky=False,
	    priority=priority
	)
	print(f"Sent notification with aliases and title: '{title}' and message: '{message}' successfully.")
	# print("="*(os.get_terminal_size()[0] - 11))
except Exception as e:
	print(f"ERROR DURING TEST: {e}")

print(f"{'='*(int(os.get_terminal_size()[0]/3))} TEST WITH DEFAULT ARGUMENTS WITHOUT VALUES {'='*(int(os.get_terminal_size()[0]/3))}")  # type: ignore

try:
	growl = Publisher(  # type: ignore
		hostname='127.0.0.1',
	    port=23053
	)

	# Register application
	growl.register()

	# Read icon if exists
	icon = Path(__file__).parent / 'logo.png'
	print(f"ICON PATH: {icon}")
	print(f"ICON PATH is file: {Path(icon).is_file()}")

	# Send notification
	title = "TEST_TITLE"
	message = "TEST WITH DEFAULT ARGUMENTS WITHOUT VALUES"
	priority = 0
	growl.publish(
	    text=message,
	    icon=Resource(str(icon)) if Path(icon).exists() else None,  # type: ignore
	    sticky=False,
	    priority=priority
	)
	print(f"Sent notification with aliases and title: '{title}' and message: '{message}' successfully.")
	# print("="*(os.get_terminal_size()[0] - 11))
except Exception as e:
	print(f"ERROR DURING TEST: {e}")

print(f"{'='*(int(os.get_terminal_size()[0]/3))} TEST WITH Binary Icon Data {'='*(int(os.get_terminal_size()[0]/3))}")  # type: ignore

try:
	growl = Publisher(  # type: ignore
	    name="Network Monitor",
	    event_defs=["Status Update"],
	    hostname='127.0.0.1',
	    port=23053
	)

	# Register application
	growl.register()

	# Read icon if exists
	icon = Path(__file__).parent / 'logo.png'
	print(f"ICON PATH: {icon}")
	print(f"ICON PATH is file: {Path(icon).is_file()}")

	icon_data = None
	if icon.exists():
		with open(icon, "rb") as f:
			icon_data = f.read()

	# Send notification
	title = "TEST_TITLE"
	message = "TEST WITH Binary Icon Data"
	priority = 0
	growl.publish(
	    name="Status Update",
	    title=title,
	    text=message,
	    icon=Resource(icon_data) if Path(icon).exists() else None,  # type: ignore
	    sticky=False,
	    priority=priority
	)
	print(f"Sent notification with title: '{title}' and message: '{message}' successfully.")
	# print("="*(os.get_terminal_size()[0] - 11))
except Exception as e:
	print(f"ERROR DURING TEST: {e}")


print(f"{'='*(int(os.get_terminal_size()[0]/3))} TEST WITH Alias {'='*(int(os.get_terminal_size()[0]/3))}")  # type: ignore

try:
	# Read icon if exists
	icon = Path(__file__).parent / 'logo.png'
	print(f"ICON PATH: {icon}")
	print(f"ICON PATH is file: {Path(icon).is_file()}")

	icon_data = None
	if icon.exists():
		with open(icon, "rb") as f:
			icon_data = f.read()

	growl = GrowlNotifier(
        applicationName="PyPIHub Sync",
        notifications=["file_changed", "sync_error", "sync_completed", "Status Update"],
        defaultNotifications=["file_changed"],
        applicationIcon=icon_data,
    )

	# Register application
	growl.register()
	
	# Send notification
	title = "TEST_TITLE"
	message = "TEST WITH Alias"
	priority = 0
	growl.notify(
	    name="Status Update",
	    title=title,
	    text=message,
	    icon=Resource(icon_data) if Path(icon).exists() else None,  # type: ignore
	    sticky=False,
	    priority=priority
	)
	print(f"Sent notification with title: '{title}' and message: '{message}' successfully.")
	print("="*(os.get_terminal_size()[0] - 11))
except Exception as e:
	traceback.print_exc()
	print(f"ERROR DURING TEST: {e}")


print("TEST COMPLETE.")