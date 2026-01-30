# coding=utf-8
# Copyright 2018 Rusty Bower
# Licensed under the Eiffel Forum License 2
from __future__ import annotations

import requests

from sopel import plugin


def display(bot, term, data, num=1):
    try:
        definition = data['list'][num - 1]['definition']
    except IndexError:
        bot.reply("Requested definition does not exist. Try a lower number.")
        return

    # Clean up definition (remove brackets used for cross-references)
    definition = definition.replace('[', '').replace(']', '')

    msg = f'[urban] {term} - {definition}'
    # Truncate if too long
    if len(msg) > 400:
        msg = msg[:397] + '...'

    bot.say(msg)


def get_definition(term):
    try:
        response = requests.get(
            f'https://api.urbandictionary.com/v0/define?term={term}',
            timeout=10
        )
        return response.json()
    except requests.RequestException:
        return None


@plugin.command('ud', 'urban')
@plugin.example('.urban fronking', '[urban] fronking - If your name is Hunter you are a fronker.')
def urban(bot, trigger):
    """Look up a term on Urban Dictionary."""
    if not trigger.group(2):
        bot.reply("Please provide a term to look up.")
        return

    term, _, num = trigger.group(2).partition('/')

    if num:
        try:
            num = int(num)
        except ValueError:
            bot.reply(f"'{num}' is not a valid definition number.")
            return

        if num < 1 or num > 10:
            bot.reply("Try a definition number in the range 1-10.")
            return

        term = term.strip()
    else:
        num = 1

    data = get_definition(term)

    if data and 'list' in data and len(data['list']) > 0:
        display(bot, term, data, num)
    else:
        bot.reply("Sorry, no results.")
