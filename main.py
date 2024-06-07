from openai import OpenAI
import do

do.client = OpenAI(api_key = "get your OpenAI key from platform.openai.com/playground")

do.run_code({0, 1, 2, 3, 4, 5, 9}, 200, "print the first 10 prime numbers")
# many other "do." functions are available
