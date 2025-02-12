# GEdit plugin to edit with GPT

This is a plugin for GEdit (GNOME Text Editor) that takes the document selection (or the whole document) as an input and replaces it with a GPT-generated content instructed by the given prompt.


## Prerequisites

This is a GNOME 3 plugin.


## Installation

The simplest plain-form installation in Linux can be done as follows:

```
mkdir -p $HOME/.local/share/gedit/plugins
cd $HOME/.local/share/gedit/plugins
git clone https://github.com/dmikushin/editgpt.git editgpt
```


## Usage

1. Enable EditGPT plugin in GEdit plugins
2. Select some text and press Ctrl+R to perform GPT edit
