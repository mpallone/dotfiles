To set up unix env on new computer, do:

1. Set up ssh keys:
   http://www.linuxproblem.org/art_9.html

2. Zip the unix-config directory
3. Zip the scripts directory

4. scp unix-config.zip and scripts.zip
   onto the new machine

5. unzip the files:
   `unzip unix-config.zip # ubuntu`
   `unzip scripts.zip #ubuntu`

6. in the ~/.bashrc (or whatever),
   add `source ~/unix-config/my-env.sh`

7. Add everything in the dot_gitconfig file
   into the new machine's .gitconfig file.
   If one doesn't exist, just type
   `cp dot_gitconfig ~/.gitconfig`

8. Sanity check that the .gitconfig
   settings are appropriate for the new
   machine. 

9. Edit one-time-config.sh as appropriate
   for the new machine, and then run it

10. Add everything in the dot_emacs file
   into the new machine's .emacs file.
   If one doesn't exist, just type
   `cp dot_emacs ~/.emacs`
   
11. Set up Sublime Text keybinds.
