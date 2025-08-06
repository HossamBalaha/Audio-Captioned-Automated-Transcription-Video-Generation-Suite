'''
========================================================================
        ╦ ╦┌─┐┌─┐┌─┐┌─┐┌┬┐  ╔╦╗┌─┐┌─┐┌┬┐┬ ┬  ╔╗ ┌─┐┬  ┌─┐┬ ┬┌─┐
        ╠═╣│ │└─┐└─┐├─┤│││  ║║║├─┤│ ┬ ││└┬┘  ╠╩╗├─┤│  ├─┤├─┤├─┤
        ╩ ╩└─┘└─┘└─┘┴ ┴┴ ┴  ╩ ╩┴ ┴└─┘─┴┘ ┴   ╚═╝┴ ┴┴─┘┴ ┴┴ ┴┴ ┴
========================================================================
# Author: Hossam Magdy Balaha
# Initial Creation Date: Aug 5th, 2025
# Last Modification Date: Aug 5th, 2025
# Permissions and Citation: Refer to the README file.
'''

import re


def CleanText(text):
  """
  Escape special characters in the text for use in FFMPEG commands.
  """
  if (not isinstance(text, str)):
    return text  # Return as-is if not a string.

  # Replace common typographic quotes with standard quotes.
  text = (
    text
    .replace("’", "'")
    .replace("‘", "'")
    .replace("“", '"')
    .replace("”", '"')
    .replace("—", "; ")
    .replace("’", "'")
    .replace("‘", "'")
    .replace("“", '"')
    .replace("”", '"')
    .replace("…", "...")
  )

  # Replace tabs with spaces.
  text = text.replace("\t", " ")

  # Replace the many spaces (but not new lines) with a single space.
  text = re.sub(r'[ ]{2,}', ' ', text)

  # Remove all special characters except for alphanumeric characters, spaces, new lines and basic punctuation.
  # Don't remove new lines.
  text = re.sub(r'[^a-zA-Z0-9\s\.]', '', text)

  return text


def EscapeText(text):
  """
  Escape special characters in the text for use in FFMPEG commands.
  """

  if (not isinstance(text, str)):
    return text  # Return as-is if not a string.

  # Escape for FFMPEG command usage.
  text = (
    text
    .replace("\\", "\\\\")
    .replace("?", "\\?")
    .replace("!", "\\!")
    .replace(":", "\\:")
    .replace(";", "\\;")
    .replace("'", "\\'")
    .replace('"', '\\"')
    .replace("(", "\\(")
    .replace(")", "\\)")
    .replace("[", "\\[")
    .replace("]", "\\]")
    .replace("{", "\\{")
    .replace("}", "\\}")
    .replace("<", "\\<")
    .replace(">", "\\>")
    .replace("$", "\\$")
    .replace("&", "\\&")
    .replace("|", "\\|")
    .replace("*", "\\*")
    .replace("~", "\\~")
    .replace(",", "\\,")
    .replace(".", "\\.")
  ).strip()

  return text


if __name__ == "__main__":
  # Example usage.
  sampleText1 = '"This is a sample text with special characters: $&|;<>()[{}]*?~\nNew line and \t tab."'
  sampleText2 = '''Don't "Welcome" ! hadn’t? everyone—patients hello;'''.upper()
  sampleText3 = '''
  Select the [suitable] voice according to the language you selected. 
  For example, if you selected (American English), you should select an American English voice!
  You will find the groups           highlighted in the voice selection dropdown?
  !@#$%^&*}{POIUYTREWQ":LKJHGFDSA?><MNBVCXZ\
  '''
  sampleText4 = '''
  In a quiet hospital nestled in the heart of a busy city,
  a young doctor named Maya sat at her desk, staring at a stack of patient files.
  The fluorescent lights buzzed faintly overhead,
  casting a sterile glow on the room around her.
  She sighed, rubbing her temples as she flipped through page after page.
  
  Maya had always dreamed of being a healer,
  someone who could make a difference in people’s lives.
  But lately, the weight of the job felt overwhelming.
  Every day brought new challenges:
  patients with complex symptoms,
  diagnoses that took too long to confirm,
  and sometimes—when time ran out—heartbreaking outcomes.
  
  Across town, in a sleek tech lab filled with glowing screens and humming servers,
  a programmer named Sam was working late into the night.
  He leaned back in his chair, sipping cold coffee from a chipped mug,
  thinking about how his work might one day save lives.
  Sam wasn’t a doctor, but he knew technology could change medicine forever.
  
  What neither Maya nor Sam realized was that their paths were about to cross—
  in ways neither of them could have imagined.
  '''
  cleanedText = CleanText(sampleText3)
  print("Original Text:\n", sampleText3)

  escapedText = EscapeText(cleanedText)
  print("Cleaned Text:\n", cleanedText)
  print("Escaped Text:\n", escapedText)
