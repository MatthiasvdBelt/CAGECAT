"""Runs the multicblaster web service

Author: Matthias van den Belt
"""

# own project imports
from multicblaster import app

### main code
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)

    # lets other computers within the same network access the web pages
    # by typing the following address in a web browser:
    #       "<ip_of_pc_where_this_module_is_ran_from>:5000"
