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

  # Replace the many spaces with a single space.
  text = re.sub(r'\s+', " ", text).strip()

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
    .replace('"', '\\"')  # Escape double quotes.
    .replace("'", "\\'")  # Escape single quotes.
    .replace("$", "\\$")  # Escape dollar sign.
    .replace("&", "\\&")  # Escape ampersand.
    .replace("|", "\\|")  # Escape pipe.
    .replace(";", "\\;")  # Escape semicolon.
    .replace("<", "\\<")  # Escape less than.
    .replace(">", "\\>")  # Escape greater than.
    .replace("(", "\\(")  # Escape left parenthesis.
    .replace(")", "\\)")  # Escape right parenthesis.
    .replace("[", "\\[")  # Escape left square bracket.
    .replace("]", "\\]")  # Escape right square bracket.
    .replace("{", "\\{")  # Escape left curly brace.
    .replace("}", "\\}")  # Escape right curly brace.
    .replace("*", "\\*")  # Escape asterisk.
    .replace("?", "\\?")  # Escape question mark.
    .replace("~", "\\~")  # Escape tilde.
    .replace("\n", " ")  # Replace new lines with spaces.
  )

  return text


if __name__ == "__main__":
  # Example usage.
  sampleText = '"This is a sample text with special characters: $&|;<>()[{}]*?~\nNew line and \t tab."'
  cleanedText = CleanText(sampleText)
  escapedText = EscapeText(cleanedText)
  print("Original Text:\n", sampleText)
  print("Cleaned Text:\n", cleanedText)
  print("Escaped Text:\n", escapedText)
