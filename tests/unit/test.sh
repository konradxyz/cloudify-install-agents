#!/bin/bash

set -ea


SCRIPT_NAME=$0

function usage_exit {
    echo 'Usage: $SCRIPT_NAME (install|uninstall|test)'
    exit 1
}

function install {
   virtualenv env
    . env/bin/activate
    pip install -r test-requirements.txt
    cd ../..
    pip install -e .
}

function uninstall {
    rm -rf env
}

function run_test {
    . env/bin/activate
    CONFIG_PATH=config.yaml
    nosetests tests/ -s
}


if [[ $# -lt 1 ]]; then
    usage_exit
fi

while getopts v opt; do
    case $opt in
        v)
            set -x
            ;;
        \?)
            usage_exit
            ;;
    esac
done
shift $((OPTIND - 1))

case $1 in
    install)
        install
        ;;
    uninstall)
        uninstall
        ;;
    test)
        run_test
        ;;
    *)
        usage_exit
        ;;
esac
