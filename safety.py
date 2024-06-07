thousand = 1000
million = thousand * thousand
pound = 100

class options:
    max_tokens = thousand * 10 # set to 0 or None for unused
    max_pennies = 3 # set to 0 or None for unused
    track_use_this_session = True
    audio = True # emergency audio alert

class log:
    prev_input_character_count, prev_output_token_count = 0, 0

# prices and rates are from June 1st 2024
class constants:
    tokens_per_character = 0.25 # approximately 4 text characters per token
    cents_per_input_token = 0.00015
    cents_per_output_token = 0.0002
    cent_to_penny = 0.79 # 1 USD cent = 0.79 GBP penny

# TODO not sure if the pricing calculation is working properly

# check if the planned request would result in excessive financial spending on tokens
# if so then produce a detailed emergency error and stop the program
# values are approximate
# pennies are GBP, and cents are USD
# prices and rates are from June 1st 2024
def check(request_input_character_count : int, request_output_token_count : int):
    # calculate text token counts
    prev_input_token_count = \
        int(log.prev_input_character_count * constants.tokens_per_character)
    request_input_token_count = \
        int(request_input_character_count * constants.tokens_per_character)
    prev_token_count = \
        prev_input_token_count + log.prev_output_token_count
    request_token_count = \
        request_input_token_count + request_output_token_count

    # calculate financial costs
    prev_input_pennies = int(prev_input_token_count * \
        constants.cents_per_input_token * constants.cent_to_penny)
    prev_output_pennies = int(log.prev_output_token_count * \
        constants.cents_per_output_token * constants.cent_to_penny)
    prev_pennies = prev_input_pennies + prev_output_pennies
    request_input_pennies = int(request_input_token_count * \
        constants.cents_per_input_token * constants.cent_to_penny)
    request_output_pennies = int(request_output_token_count * \
        constants.cents_per_output_token * constants.cent_to_penny)
    request_pennies = request_input_pennies + request_output_pennies

    # check if the planned request would result in excessive financial spending on tokens
    # if so then produce a detailed emergency error and stop the program
    tokens_good = (not options.max_tokens) or \
        (prev_token_count + request_token_count <= options.max_tokens)
    pennies_good = (not options.max_pennies) or \
        (prev_pennies + request_pennies <= options.max_pennies)
    if tokens_good and pennies_good:
        # safeguard did not trigger, track spending for this session
        if options.track_use_this_session:
            log.prev_input_character_count += request_input_character_count
            log.prev_output_token_count += request_output_token_count
    else: # safeguard triggered, produce a detailed error and stop the program
        check_fail(prev_input_token_count, prev_token_count,
            request_input_token_count, request_output_token_count,
            request_token_count,
            prev_input_pennies, prev_output_pennies,
            prev_pennies,
            request_input_pennies, request_output_pennies,
            request_pennies)

def check_fail(
    prev_input_token_count : int, prev_token_count : int,
    request_input_token_count : int, request_output_token_count : int,
    request_token_count : int,
    prev_input_pennies : int, prev_output_pennies : int, prev_pennies : int,
    request_input_pennies : int, request_output_pennies : int, request_pennies : int):

    # only listing significant costs (1 penny or more)
    minor_prev_cost = prev_pennies == 0
    minor_request_cost = request_input_pennies + request_output_pennies == 0

    def report_exceed(cause : bool = False) -> str:
        text = "\n\nThis request would " + \
            ("cause the session to " if cause else "") + "exceed the safeguard of "
        if options.max_tokens: # only max_tokens is in use
            text += str(options.max_tokens) + " tokens"
            if options.max_pennies: # both are in use
                text += " or " + penny_to_str(options.max_pennies)
        else: # only max_pennies is in use
            text += penny_to_str(options.max_pennies)
        return text + ".\n\n"

    error_text = "EMERGENCY ERROR" + \
        "\nvalues below are approximate, prices are in GBP" + \
        "\nprices and rates are from June 1st 2024"

    # token counts and costs
    if minor_prev_cost and not minor_request_cost:
        error_text += "\ncosts from earlier this session are less than a penny" + \
        report_exceed() + \
        report(request_input_token_count, request_output_token_count,
            request_input_pennies, request_output_pennies)
    elif minor_request_cost and not minor_prev_cost:
        error_text += "\nthis request costs less than a penny" + \
        report_exceed() + \
        report(prev_input_token_count, log.prev_output_token_count,
            prev_input_pennies, prev_output_pennies)
    else:
        # previous costs and the requested cost are significant
        error_text += report_exceed(True) + "\nPreviously this session:\n\n" + \
        report(prev_input_token_count, log.prev_output_token_count,
            prev_input_pennies, prev_output_pennies) + \
        "\n\n\nThis request:\n\n" + \
        report(request_input_token_count, request_output_token_count,
            request_input_pennies, request_output_pennies) + \
        "\n\n\ntotal requested and previous tokens: " + \
        str(prev_token_count + request_token_count) + \
        "\ntotal cost would have been: " + \
        penny_to_str(prev_pennies + request_pennies) + "\n"

    # document the stack as a list of strings
    # starting from this functions caller
    error_text += "\n\n" + stack_debug()

    # emergency audio to get the users attention
    alert_audio()

    # output the error
    print("\n" + error_text + "\n")
    raise SystemExit(error_text + "\n.")

def report(input_token_count : int, output_token_count : int,
    input_pennies : int, output_pennies : int) -> str:
    text = "input tokens: " + str(input_token_count) + \
        "\noutput tokens: " + str(output_token_count) + \
        "\ntotal tokens: " + str(input_token_count + output_token_count) + \
        "\ninput cost: " + penny_to_str(input_pennies) + \
        "\noutput cost: " + penny_to_str(output_pennies) + \
        "\ntotal cost: " + penny_to_str(input_pennies + output_pennies)
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
    stack_frame_names = stack_frame_names[1:] # don't include the "safe" module
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
    if options.audio:
        import platform
        if platform.system() == "Windows":
            import winsound
            winsound.Beep(700, 2000)
        else:
            print('\a') # cross-platform "beep"

def penny_to_str(GBP_penny : int) -> str:
    return "£" + str(int(GBP_penny) / 100)
