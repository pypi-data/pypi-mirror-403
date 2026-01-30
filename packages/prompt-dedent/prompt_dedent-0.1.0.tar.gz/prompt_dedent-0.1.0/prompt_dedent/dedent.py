import logging
from typing import Any

# Create a logger for this module
logger = logging.getLogger(__name__)




INSERT_OPEN = "<1Ns3rT!!>" # Chosen as random unique character string to minimize likelihood of collisions with text within an actual message.
INSERT_CLOSE = "</1Ns3rT!!>"


def insert(obj: Any) -> str:
    """ Wrap your variable in this function when placing the variable inside of an f-string expression used in an dedent block. This allows for the f-string variable to have line breaks that don't have the base indentation.

    NOTE: The entire inserted block will adopt the indentation before the insert() function! So you can easily add an indented block.

    Represents the object as a string and wrap it in INSERT_OPEN and INSERT_CLOSE. """
    return f"{INSERT_OPEN}{obj}{INSERT_CLOSE}"

def dedent(input_text: str, remove_trailing_whitespace: bool = True) -> str:
    """ Allows long, multi-line strings to be written in code with proper indentation.
    
    Rules:
        - The first line must be empty.
        - The second line determines the base indentation.
        - Lines with only whitespace will be replaced with an empty string "".
        - Lines with content characters must include at least the base indentation.
        - Trailing whitespace (including empty lines) will be removed from the output.
    
    Inserting f-string expressions:
        - If you're inserting a multi-line string into the text block via an f-string expression, the inserted text will not have the base indentation. To address this issue, wrap your f-string expression in <insert></insert> blocks. These are custom "HTML" tags that I've implemented which will allow multi-line f-string text to be inserted into a dedent text block. The entire f-string variable text will be indented according to the indentation amount before the opening <insert> tag. Note that <insert> cannot have content characters before it and </insert> canot have any characters after it.

    Tips:
        - In VS Code, it looks like when you hit enter, the default indentation gets set to be WHERE the opening triple quote \""" is. So writing your text as:
            dedent(
                \"""
                Your text here.
                \"""
            )
          is wayyyyyy easier than writing your text like this:
            dedent(\"""
                Your text here.
                \"""
            )
          If you do the second option, every time you hit enter to add a new line you have to backspace like a million times to get back to the base indentation. Trust me... it doesn't sound that bad, but formatting your text the first way will save a lot of time and headache.
    """
    
    def get_indentation(line: str) -> str:
        """ Returns the indentation of the line. """
        if line.lstrip() == "": # If the line is only empty space, return that as the base indentation.
            return line
        return line[:-len(line.lstrip())] # Otherwise, return the space before the first non-whitespace character. Note, that the conditional check is required because if the whole line is empty, this will go from line[:-0] which won't capture anything.
    
    def remove_indentation(line: str, indentation: str) -> str:
        """ Removes base indentation from the line. """
        return line[len(indentation):]

    lines = input_text.split("\n")
    
    if len(lines) < 2:
        raise ValueError("String must have leading line before actual content.")

    # Check to make sure the first line is empty
    first_line = lines[0]   
    if first_line.strip() != "":
        raise ValueError("String not formatted correctly! First line must be empty.")
    
    # Look at the second line to determine the indentation amount
    second_line = lines[1]
    base_indentation = get_indentation(second_line)

    # Loop across lines
    dedented_lines = []
    insert_region_is_open: bool = False # Does the current line belong to an <insert></insert> region?
    insert_region_indentation: str | None = None
    
    for line in lines[1:]:
        # Convert all non-content lines (within insert region or not) to an empty string
        if line.strip() == "":
            # Lines with only whitespace will be replaced with an empty string.
            line = ""
        
        #region: Handle <insert></insert> regions
        # Look for opening tags
        num_open_tags = line.count(INSERT_OPEN)
        if num_open_tags == 0:
            line_has_open_tag = False
        elif num_open_tags == 1:
            line_has_open_tag = True
            if insert_region_is_open:
                raise ValueError("Cannot have an opening <insert> tag within another <insert> region. Did you forget to close the previous <insert> region?")
            if not line.lstrip().startswith(INSERT_OPEN):
                raise ValueError("Cannot have non-whitespace text before the <insert> tag on this line.")
            insert_region_is_open = True
        else:
            raise ValueError("Cannot have more than one <insert> opening tag in a given line!")
        
        # Handle lines within the insert region...
        if insert_region_is_open:
            if line_has_open_tag:
                """ Line opens an insert region... """
                # Determine the indentation of the region based on the indentation before the <insert> tag
                insert_region_is_open = True
                line = remove_indentation(line, base_indentation) # Make sure to modify line in place (rather than using a new variable) because you will need to post process the line again if it also has a closing tag.
                insert_region_indentation = get_indentation(line) # Get the indentation before the <insert> tag
                line = line.replace(INSERT_OPEN, "") # Remove the insert tag from the line
            else:
                """ Lines within the insert region, excluding the opening line... """
                if insert_region_indentation is None: # Make sure you use "is None" instead of just the truthiness of inserted_region_indentation, because the inserted_region_indentation could very well be an empty string.
                    raise RuntimeError("Indentation for insert region not set.")
                line = insert_region_indentation + line

        # Look for closing tags
        num_close_tags = line.count(INSERT_CLOSE)
        if num_close_tags == 0:
            line_has_close_tag = False
        elif num_close_tags == 1:
            line_has_close_tag = True
            if not insert_region_is_open:
                raise ValueError("Closing </insert> tag detected when an insert region was never opened.")
            if not line.endswith(INSERT_CLOSE):
                raise ValueError("Line should not have any non-whitespace text after a closing </insert> tag.")

            # Close the insert region and remove the closing insert tag
            insert_region_is_open = False
            line = line[:-len(INSERT_CLOSE)]
        else:
            raise ValueError("Cannot have more than one <insert> opening tag in a given line!")
        #endregion
        
        # Remove base indentation from "regular" lines (not within an insert region)
        if not insert_region_is_open and not line_has_close_tag:
            # Make sure the line has at least the base indentation
            if line.strip() != "" and not line.startswith(base_indentation):
                raise ValueError("All non-empty lines must start with at least the base indentation.")
            
            # Remove the base indentation
            line = line[len(base_indentation):]
        
        # Append the processed line to new_lines
        dedented_lines.append(line)

    # Validate dedented_lines
    # After all lines, make sure there isn't still an open insert region
    if insert_region_is_open:
        raise ValueError("<insert> region was never closed!")    
    
    output = "\n".join(dedented_lines)

    if not remove_trailing_whitespace:
        return output

    output_without_trailing_whitespace = output.rstrip()

    # Log what we removed
    removed_trailing_whitespace = output[len(output_without_trailing_whitespace):]
    num_empty_lines = removed_trailing_whitespace.count("\n")
    if num_empty_lines > 1:
        logger.warning(f"Removed {num_empty_lines} empty lines from the end of dedented text.")

    return output_without_trailing_whitespace

