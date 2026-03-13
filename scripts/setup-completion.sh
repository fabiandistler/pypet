#!/bin/bash

# Configuration
VERSION="1.0.0"
SCRIPT_NAME="pypet-completion"
COMPLETION_DIR="/etc/bash_completion.d"
LOCAL_COMPLETION_DIR="$HOME/.bash_completion.d"

# Function to generate the completion script
generate_completion() {
    # We use click's built-in bash completion support
    # For Click 8.x, the command to generate completion is:
    # _PYPET_COMPLETE=bash_source pypet
    
    cat << 'EOF'
_pypet_completion() {
    local IFS=$'\n'
    local response

    response=$(env _PYPET_COMPLETE=bash_complete COMP_WORDS="${COMP_WORDS[*]}" COMP_CWORD=$COMP_CWORD pypet)

    for item in $response; do
        if [[ $item == _lowline_* ]]; then
            item=${item#_lowline_}
        fi
        COMPREPLY+=("$item")
    done

    return 0
}

complete -F _pypet_completion pypet
EOF
}

# Install function
install_completion() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if [ -d "$COMPLETION_DIR" ] && [ -w "$COMPLETION_DIR" ]; then
            generate_completion > "$COMPLETION_DIR/pypet"
            echo "Installed global bash completion to $COMPLETION_DIR/pypet"
        else
            mkdir -p "$LOCAL_COMPLETION_DIR"
            generate_completion > "$LOCAL_COMPLETION_DIR/pypet"
            echo "Installed local bash completion to $LOCAL_COMPLETION_DIR/pypet"
            echo "Make sure to source it in your .bashrc:"
            echo "  source $LOCAL_COMPLETION_DIR/pypet"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS with brew bash-completion
        BREW_COMPLETION_DIR="$(brew --prefix)/etc/bash_completion.d"
        if [ -d "$BREW_COMPLETION_DIR" ] && [ -w "$BREW_COMPLETION_DIR" ]; then
            generate_completion > "$BREW_COMPLETION_DIR/pypet"
            echo "Installed bash completion to $BREW_COMPLETION_DIR/pypet"
        else
            mkdir -p "$LOCAL_COMPLETION_DIR"
            generate_completion > "$LOCAL_COMPLETION_DIR/pypet"
            echo "Installed local bash completion to $LOCAL_COMPLETION_DIR/pypet"
            echo "Make sure to source it in your .bash_profile or .bashrc:"
            echo "  source $LOCAL_COMPLETION_DIR/pypet"
        fi
    fi
}

# Main logic
case "$1" in
    generate)
        generate_completion
        ;;
    install)
        install_completion
        ;;
    *)
        echo "Usage: $0 {generate|install}"
        exit 1
        ;;
esac
