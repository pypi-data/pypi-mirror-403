import argparse

from devbricksxai.generativeai.roles.advisor import Advisor
from devbricksxai.generativeai.roles.advisors.chatgpt import ADVISOR_GPT
from devbricksxai.generativeai.roles.artisans.escort import InEscort, OutEscort
from devbricksxai.generativeai.roles.artisans.escorts.cloud_storage import ESCORT_CLOUD_STORAGE
from devbricksxai.generativeai.roles.artisans.escorts.url import ESCORT_URL
from devbricksxai.generativeai.roles.artisans.historian import Historian
from devbricksxai.generativeai.roles.artisans.historians.firestore import HISTORIAN_FIRESTORE
from devbricksxai.generativeai.roles.artisans.musician import Musician
from devbricksxai.generativeai.roles.artisans.musicians.suno_musician import MUSICIAN_SUNO
from devbricksxai.generativeai.roles.artisans.painter import Painter
from devbricksxai.generativeai.roles.artisans.painters.dalle import PAINTER_DALL_E
from devbricksxai.generativeai.roles.character import list_characters, Role, init_characters, get_character_by_name
from devbricksxai.generativeai.settings.aisettings import init_ai_settings, DEFAULT_AI_SETTINGS_FILE, get_ai_settings
from devbricksxai.generativeai.taskforce import TaskForce
from devbricksx.development.log import debug

def append_task_force_options_to_parse(ap: argparse.ArgumentParser):

    available_advisors = list_characters(Role.ADVISOR)
    available_painters = list_characters(Role.ARTISAN, in_instances=[Painter])
    available_musicians = list_characters(Role.ARTISAN, in_instances=[Musician])
    available_historians = list_characters(Role.ARTISAN, in_instances=[Historian])
    available_in_escorts = list_characters(Role.ARTISAN, in_instances=[InEscort])
    available_out_escorts = list_characters(Role.ARTISAN, in_instances=[OutEscort])
    available_characters =  [c.name for c in list_characters()]

    tf_opts_group = ap.add_argument_group('AI Taskforce arguments')

    tf_opts_group.add_argument("-a", "--advisor",
                               default=ADVISOR_GPT,
                               help="specify generative AI Advisor to use. [{}]".format(
                                   ", ".join(a.alias for a in available_advisors)))
    tf_opts_group.add_argument("-p", "--painter",
                               default=PAINTER_DALL_E,
                               help="specify generative AI Painter to use. [{}]".format(
                                   ", ".join(p.alias for p in available_painters)))
    tf_opts_group.add_argument("-m", "--musician",
                               default=MUSICIAN_SUNO,
                               help="specify generative AI Musician to use. [{}]".format(
                                   ", ".join(m.alias for m in available_musicians)))
    tf_opts_group.add_argument("-hi", "--historian",
                               default=HISTORIAN_FIRESTORE,
                               help="specify generative AI Historian to use. [{}]".format(
                                   ", ".join(h.alias for h in available_historians)))
    tf_opts_group.add_argument("-ie", "--in-escort",
                               default=ESCORT_URL,
                               help="specify generative AI Escort (In direction) to use. [{}]".format(
                                   ", ".join(e.alias for e in available_in_escorts)))
    tf_opts_group.add_argument("-oe", "--out-escort",
                               default=ESCORT_CLOUD_STORAGE,
                               help="specify generative AI Escort (Out direction) to use. [{}]".format(
                                   ", ".join(e.alias for e in available_out_escorts)))

    tf_opts_group.add_argument("-am", "--add-members",
                               nargs='+',
                               help="add generative AI characters. [{}]".format(
                                   ", ".join(c for c in available_characters)))

    tf_opts_group.add_argument('-cp', "--character-parameter",
                               nargs=3,
                               action='append',
                               metavar=('ALIAS', 'PARAM_NAME', 'PARAM_VALUE'),
                               help='provide parameters for character: character_alias, param_name, and param_value')

    tf_opts_group.add_argument("-sf", "--settings-file",
                               default=DEFAULT_AI_SETTINGS_FILE,
                               help="specify settings file for AI.")

def init_generative_ai_args(args_parse):
    append_task_force_options_to_parse(args_parse)

def init_generative_ai(args):
    debug("using settings file: {}".format(args.settings_file))
    init_ai_settings(args.settings_file)
    init_characters()

    if args.character_parameter is not None:
        for param_group in args.character_parameter:
            alias, param_name, param_value = param_group
            debug(f"set [{alias}]'s parameter: {param_name} = {param_value}")

            member = get_character_by_name(alias)
            if member is not None:
                member.add_parameter(param_name, param_value)


def create_task_force_from_arguments(name, args):
    task_force = TaskForce(name)

    advisor = None
    if args.advisor is not None:
        advisor = get_character_by_name(args.advisor, Advisor)
    if advisor is None:
        advisor = get_character_by_name(ADVISOR_GPT, Advisor)

    if advisor is not None:
        task_force.add_member(advisor)
        debug(f"adding advisor to taskforce: {advisor}")

    painter = None
    if args.painter is not None:
        painter = get_character_by_name(args.painter, Painter)
    if painter is None:
        painter = get_character_by_name(PAINTER_DALL_E, Painter)

    if painter is not None:
        task_force.add_member(painter)
        debug(f"adding painter to taskforce: {painter}")

    musician = None
    if args.musician is not None:
        musician = get_character_by_name(args.musician, Musician)
    if painter is None:
        musician = get_character_by_name(MUSICIAN_SUNO, Musician)

    if musician is not None:
        task_force.add_member(musician)
        debug(f"adding musician to taskforce: {musician}")

    historian = None
    if args.historian is not None:
        historian = get_character_by_name(args.historian, Historian)
    if historian is None:
        historian = get_character_by_name(HISTORIAN_FIRESTORE, Historian)

    if historian is not None:
        task_force.add_member(historian)
        debug(f"adding historian to taskforce: {historian}")

    in_escort = None
    if args.in_escort is not None:
        in_escort = get_character_by_name(args.in_escort, InEscort)
    if in_escort is None:
        in_escort = get_character_by_name(ESCORT_URL, InEscort)

    if in_escort is not None:
        task_force.add_member(in_escort)
        debug(f"adding escort(in) to taskforce: {in_escort}")

    out_escort = None
    if args.out_escort is not None:
        out_escort = get_character_by_name(args.out_escort, OutEscort)
    if out_escort is None:
        out_escort = get_character_by_name(ESCORT_CLOUD_STORAGE, OutEscort)

    if out_escort is not None:
        task_force.add_member(out_escort)
        debug(f"adding escort(out) to taskforce: {out_escort}")

    if args.add_members is not None and len (args.add_members) > 0:
        for member in args.add_members:
            c = get_character_by_name(member)
            if c is not None:
                debug(f"adding character to taskforce: {c}")

                task_force.add_member(c)

    # if args.character_parameter is not None:
    #     for param_group in args.character_parameter:
    #         alias, param_name, param_value = param_group
    #         debug(f"set [{alias}]'s parameter: {param_name} = {param_value}")
    #
    #         member = task_force.get_member(alias)
    #         if member is not None:
    #             member.add_parameter(param_name, param_value)

    return task_force

def print_task_force_info(task_force: TaskForce, print_func):
    print_func('==============================================')
    print_func('|              AI TaskForce                  |')
    print_func('==============================================')
    print_func(f'Name: {task_force.name}')
    print_func('----------------------------------------------')
    print_func('Members')
    print_func('----------------------------------------------')
    for m in task_force.members:
        print_func(f"{m}")
    print_func('')