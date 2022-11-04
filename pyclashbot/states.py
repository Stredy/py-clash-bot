import time
from typing import Literal

from pyclashbot.battlepass_rewards_collection import collect_battlepass_rewards
from pyclashbot.card_mastery_collection import collect_card_mastery_rewards
from pyclashbot.clashmain import (
    check_if_in_battle_with_delay,
    check_if_on_first_card_page,
    get_to_account,
    get_to_card_page,
    handle_card_mastery_notification,
    handle_gold_rush_event,
    open_chests,
    start_2v2,
    wait_for_battle_start,
    wait_for_clash_main_menu,
)
from pyclashbot.client import (
    click,
    orientate_terminal,
)
from pyclashbot.deck import randomize_and_select_deck_2
from pyclashbot.fight import (
    check_if_end_screen_is_exit_bottom_left,
    check_if_end_screen_is_ok_bottom_middle,
    check_if_past_game_is_win,
    fight,
    leave_end_battle_window,
)
from pyclashbot.launcher import restart_and_open_clash
from pyclashbot.level_up_reward_collection import collect_level_up_rewards
from pyclashbot.logger import Logger
from pyclashbot.request import (
    check_if_on_clan_page,
    get_to_clash_main_from_clan_page,
    request_random_card_from_clash_main,
)
from pyclashbot.upgrade import get_to_clash_main_from_card_page, upgrade_current_cards
from pyclashbot.war import handle_war_attacks


def detect_state(logger):
    # Method for detecting the state of the client in a given moment
    # sourcery skip: extract-duplicate-method
    # if we're on clan page get back to clash main and return
    if check_if_on_clan_page():
        if get_to_clash_main_from_clan_page(logger) == "restart":
            return "restart"
        time.sleep(1)
        return "clashmain"

    # if we're on card page get back to clash main and return
    if check_if_on_first_card_page():
        if get_to_clash_main_from_card_page(logger) == "restart":
            return "restart"
        time.sleep(1)
        return "clashmain"

    # if we're in battle return fighting
    if check_if_in_battle_with_delay():
        return "fighting"

    # if we're on end fight screen condition 1 (exit in bottom left)
    if check_if_end_screen_is_exit_bottom_left():
        click(79, 625)
        time.sleep(1)
        if wait_for_clash_main_menu(logger) == "restart":
            return "restart"
        return "clashmain"

    # if we're on end fight screen condition 2 (OK in bottom middle)
    if check_if_end_screen_is_ok_bottom_middle():
        click(206, 594)
        time.sleep(1)
        if wait_for_clash_main_menu(logger) == "restart":
            return "restart"
        return "clashmain"

    # if none of these conditions are met return "restart"
    return "restart"


def state_tree(
    jobs: list[str], logger: Logger, ssid_max: int, ssid: int, state: str
) -> tuple[str, int]:
    """
    Method for the state tree of the program

    Args:
        jobs (list[str]): List of jobs to be done
        logger (Logger): Logger object
        ssid (int): Session ID
        state (str): Current state of the program

    Returns:
        tuple[str, int]: Tuple of the next state and the next session ID
    """
    if state == "clashmain":

        state = state_clashmain(
            logger=logger, ssid_max=ssid_max, account_number=ssid, jobs=jobs
        )

        # Increment account number, loop back to 0 if it's ssid_max
        ssid = ssid + 1 if ssid < ssid_max else 0

    elif state == "startfight":
        state = (
            state_startfight(logger, random_deck="Randomize Deck" in jobs)
            if "Fight" in jobs
            else "upgrade"
        )

    elif state == "fighting":
        state = state_fight(logger)

    elif state == "endfight":
        state = state_endfight(logger)

    elif state == "upgrade":
        state = (
            state_upgrade(logger) if "Upgrade" in jobs else "card mastery collection"
        )

    elif state == "request":
        state = (
            state_request(logger) if "Request" in jobs else "level up reward collection"
        )

    elif state == "restart":
        state = state_restart(logger)

    elif state == "card mastery collection":
        state = (
            state_card_mastery_collection(logger)
            if "card mastery collection" in jobs
            else "request"
        )

    elif state == "level up reward collection":
        state = (
            state_level_up_reward_collection(logger)
            if "level up reward collection" in jobs
            else "battlepass reward collection"
        )

    elif state == "battlepass reward collection":
        state = (
            state_battlepass_collection(logger)
            if "battlepass reward collection" in jobs
            else "war"
        )

    elif state == "war":
        state = state_war(logger) if "war" in jobs else "clashmain"

    return (state, ssid)


def state_war(logger) -> Literal["restart", "clashmain"]:
    return "restart" if handle_war_attacks(logger) == "restart" else "clashmain"


def state_battlepass_collection(logger) -> Literal["restart", "war"]:
    return "restart" if collect_battlepass_rewards(logger) == "restart" else "war"


def state_level_up_reward_collection(
    logger,
) -> Literal["restart", "battlepass reward collection"]:
    # Method for level up reward collection state of the program

    # state_level_up_reward_collection state starts on clash main and ends on clash main
    if collect_level_up_rewards(logger) == "restart":
        return "restart"
    return "battlepass reward collection"


def state_card_mastery_collection(logger) -> Literal["restart", "request"]:
    # Method for the card mastery collection state of the program

    # card_mastery_collection state starts on clash main and ends on clash main
    if collect_card_mastery_rewards(logger) == "restart":
        return "restart"
    return "request"


def state_restart(logger) -> Literal["clashmain"]:
    # Method for the restart state of the program

    # Restart state restarts Memu and MeMU Multi Manager, opens clash, and waits for the clash main menu to appear.
    # clear_log()
    orientate_terminal()
    logger.change_status("Restarting")

    if restart_and_open_clash(logger) == "restart":
        restart_and_open_clash(logger)
    return "clashmain"


def state_clashmain(
    logger, ssid_max, account_number, jobs
) -> Literal["restart", "startfight"]:
    # Method for the clash royale main menu state of the program

    # Clashmain state gets to the correct account of the current state then
    # opens their chests

    logger.change_status("On clash main")
    handle_gold_rush_event(logger)

    # Get to correct account if more than one account is being used
    if ssid_max <= 1 and get_to_account(logger, account_number) == "restart":
        return "restart"

    time.sleep(3)

    # Open chests
    if "Open Chests" in jobs:
        open_chests(logger)
    time.sleep(3)
    return "startfight"


def state_startfight(logger, random_deck=True) -> Literal["restart", "fighting"]:
    # Method for the starting of a fight state of the program

    # Begins on clash main, ends in the beginning of a fight

    logger.change_status("Starting a fight")

    # make a random deck
    if random_deck and randomize_and_select_deck_2(logger) == "restart":
        return "restart"
    # Start 2v2 quickmatch
    if start_2v2(logger) == "restart" or wait_for_battle_start(logger) == "restart":
        return "restart"
    return "fighting"


def state_fight(logger) -> Literal["restart", "endfight"]:
    # Method for the state of the program when fighting

    # Method that plays cards with certain logic until the fight is over then
    # returns to the clash royale main screen

    logger.change_status("Fighting")
    logger.add_fight()

    if fight(logger) == "restart":
        return "restart"

    if leave_end_battle_window(logger) == "restart":
        return "restart"
    return "endfight"


def state_endfight(logger) -> Literal["upgrade"]:
    # Method for the state of the program after a fight

    # Checks if the last battle was a win or loss then adds this to the logger tally
    # Starts and ends on the clash royale main menu

    logger.change_status("Post fight")

    check_if_past_game_is_win(logger)
    return "upgrade"


def state_upgrade(logger) -> Literal["restart", "card mastery collection"]:
    # Method for the state of the program when upgrading cards

    # Starts on the clash royale main menu and ends on the clash royale main
    # menu

    logger.change_status("Upgrading cards")

    handle_card_mastery_notification()

    # Get to card page
    if get_to_card_page(logger) == "restart":
        return "restart"

    # Upgrade user cards
    upgrade_current_cards(logger)

    # return to clash main
    if get_to_clash_main_from_card_page(logger) == "restart":
        return "restart"

    return "card mastery collection"


def state_request(logger) -> Literal["restart", "level up reward collection"]:
    # Method for the state of the program when requesting cards
    # Request method goes to clan page, requests a random card if request is
    # available, then returns to the clash royale main menu

    logger.change_status("Requesting card")
    if request_random_card_from_clash_main(logger) == "restart":
        return "restart"

    return "level up reward collection"
