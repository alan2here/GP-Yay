# prices and rates are from 2024 June 1st
class constants:
    thousand = 1000
    million = thousand * thousand

    # currency values
    milliPennies_per_penny = thousand
    milliPennies_per_pound = milliPennies_per_penny * 100
    pennies_per_cent = 0.79 # 0.79 GBP penny = 1 USD cent

    # neural values
    tokens_per_character = 0.25 # approximately 4 text characters per token
    cents_per_input_token = 0.00015
    cents_per_output_token = 0.0002

    # combined values
    milliPennies_per_input_token = cents_per_input_token * pennies_per_cent * milliPennies_per_penny
    milliPennies_per_output_token = cents_per_output_token * pennies_per_cent * milliPennies_per_penny

def set(max_tokens : int = constants.thousand * 10,
    max_milliPennies : int = int(constants.milliPennies_per_penny / 2),
    track_this_session : bool = True, audio_alert = True):
    options.max_tokens = max_tokens
    options.max_milliPennies = max_milliPennies
    options.track_this_session = track_this_session
    options.audio_alert = audio_alert
    options.are_set = True

class options:
    max_tokens : int
    max_milliPennies : int
    track_this_session : bool
    audio_alert : bool
    are_set : bool = False

class log:
    prev_input_character_count, prev_output_token_count = 0, 0

# check if the planned request would result in excessive financial spending on tokens
# if so then produce a detailed emergency error and stop the program
# values are approximate
# pennies are GBP, and cents are USD
# prices and rates are from 2024 June 1st
def check(request_input_character_count : int, request_output_token_count : int):
    if not options.are_set:
        raise RuntimeError("call safety.set() first, " +
            "probably just once and at the start of your code")

    # calculate text token counts
    prev_input_token_count = \
        int(log.prev_input_character_count * constants.tokens_per_character)
    request_input_token_count = \
        int(request_input_character_count * constants.tokens_per_character)

    # calculate financial costs
    prev_input_milliPennies = \
        int(prev_input_token_count * constants.milliPennies_per_input_token)
    prev_output_milliPennies = \
        int(log.prev_output_token_count * constants.milliPennies_per_output_token)
    request_input_milliPennies = \
        int(request_input_token_count * constants.milliPennies_per_input_token)
    request_output_milliPennies = \
        int(request_output_token_count * constants.milliPennies_per_output_token)

    # check if the planned request would result in excessive financial spending on tokens
    # if so then produce a detailed emergency error and stop the program
    tokens_good = (not options.max_tokens) or \
        (prev_input_token_count + log.prev_output_token_count +
        request_input_token_count + request_output_token_count <= options.max_tokens)
    pennies_good = (not options.max_milliPennies) or \
        (prev_input_milliPennies + prev_output_milliPennies +
        request_input_milliPennies + request_output_milliPennies <= options.max_milliPennies)
    if tokens_good and pennies_good:
        # safeguard did not trigger, track spending for this session
        if options.track_this_session:
            log.prev_input_character_count += request_input_character_count
            log.prev_output_token_count += request_output_token_count
    else: # safeguard triggered, produce a detailed error and stop the program
        check_fail(prev_input_token_count, log.prev_output_token_count,
            request_input_token_count, request_output_token_count,
            prev_input_milliPennies, prev_output_milliPennies,
            request_input_milliPennies, request_output_milliPennies)

def check_fail(
    prev_input_token_count : int, prev_output_token_count : int,
    request_input_token_count : int, request_output_token_count : int,
    prev_input_milliPennies : int, prev_output_milliPennies : int,
    request_input_milliPennies : int, request_output_milliPennies : int):

    # only listing significant costs (1 penny or more)
    minor_prev_cost = prev_input_milliPennies + prev_output_milliPennies == 0
    minor_request_cost = request_input_milliPennies + request_output_milliPennies == 0

    def report_exceed(cause : bool = False) -> str:
        text = "\n\nThis request would " + \
            ("cause the session to " if cause else "") + "exceed the safeguard of "
        if options.max_tokens: # only max_tokens is in use
            text += str(options.max_tokens) + " tokens"
            if options.max_milliPennies: # both are in use
                text += " or " + milliPennies_to_str(options.max_milliPennies)
        else: # only max_pennies is in use
            text += milliPennies_to_str(options.max_milliPennies)
        return text + ".\n\n"

    error_text = "EMERGENCY ERROR" + \
        "\nvalues below are approximate, prices are in GBP" + \
        "\nprices and rates are from June 1st 2024"

    # token counts and costs
    if minor_prev_cost and not minor_request_cost:
        error_text += "\ncosts from earlier this session are less than a milliPenny" + \
        report_exceed() + \
        report(request_input_token_count, request_output_token_count,
            request_input_milliPennies, request_output_milliPennies)
    elif minor_request_cost and not minor_prev_cost:
        error_text += "\nthis request costs less than a milliPenny" + \
        report_exceed() + \
        report(prev_input_token_count, log.prev_output_token_count,
            prev_input_milliPennies, prev_output_milliPennies)
    else:
        # previous costs and the requested cost are significant
        error_text += report_exceed(True) + "\nPreviously this session:\n\n" + \
        report(prev_input_token_count, log.prev_output_token_count,
            prev_input_milliPennies, prev_output_milliPennies) + \
        "\n\n\nThis request:\n\n" + \
        report(request_input_token_count, request_output_token_count,
            request_input_milliPennies, request_output_milliPennies) + \
        "\n\n\ntotal requested and previous tokens: " + \
        str(prev_input_token_count + prev_output_token_count +
            request_input_token_count + request_output_token_count) + \
        "\ntotal cost would have been: " + \
        milliPennies_to_str(prev_input_milliPennies + prev_output_milliPennies +
            request_input_milliPennies + request_output_milliPennies) + "\n"

    # document the stack as a list of strings
    # starting from this functions caller
    error_text += "\n\n" + stack_debug()

    # emergency audio to get the users attention
    alert_audio()

    # output the error
    print("\n" + error_text + "\n")
    raise SystemExit(error_text + "\n.")

def report(input_token_count : int, output_token_count : int,
    input_milliPennies : int, output_milliPennies : int) -> str:
    text = "input tokens: " + str(input_token_count) + \
        "\noutput tokens: " + str(output_token_count) + \
        "\ntotal tokens: " + str(input_token_count + output_token_count) + \
        "\ninput cost: " + milliPennies_to_str(input_milliPennies) + \
        "\noutput cost: " + milliPennies_to_str(output_milliPennies) + \
        "\ntotal cost: " + milliPennies_to_str(input_milliPennies + output_milliPennies)
    return text

# document the stack as a list of strings
# starting from this functions caller
def stack_debug() -> str:
    # gather stack frame names
    import inspect
    frame = inspect.currentframe()
    stack_frame_names = []
    stage = 0
    while stage == 0:
        frame = frame.f_back
        if frame == None: # end of the stack
            stage = 2
        elif frame.f_locals.__contains__("__name__"):
            module_path = frame.f_locals["__file__"]
            stack_frame_names.append("module: " + module_path[module_path.rfind("\\") + 1:])
            stage = 1
        else:
            co_name = frame.f_code.co_name
            if co_name[0] == "_" or co_name[:3] == "run":
                stage = 1
            else:
                stack_frame_names.append("func: " + co_name)
    stack_frame_names = stack_frame_names[2:] # don't include "stack_debug" or "safe"
    extra_names = ""
    while stage <= 1: # summarize the rest of the stack more
        frame = frame.f_back
        if frame == None:
            stage = 2
        elif frame.f_locals.__contains__("__name__"):
            module_path = frame.f_locals["__file__"]
            extra_names += module_path[module_path.rfind("\\") + 1:] + ", "
        else:
            extra_names += frame.f_code.co_name + ", "
    stack_frame_names.append(extra_names[:-2])

    # putting it all together
    stack_text = "The stack is as follows " + \
    "(not including this \"check\" function or the safety module):\n"
    for frame_name in stack_frame_names:
        stack_text += "\n" + frame_name

    return stack_text

# emergency audio to get the users attention
def alert_audio():
    if options.audio_alert:
        import platform
        if platform.system() == "Windows":
            import winsound
            winsound.Beep(700, 2000)
        else:
            print('\a') # cross-platform "beep"

def milliPennies_to_str(milliPennies : int) -> str:
    if type(milliPennies) is float: raise TypeError
    return "£{:.5f}".format(milliPennies / # anti-scientific notation F-string
        constants.milliPennies_per_pound).rstrip('0').rstrip('.')
