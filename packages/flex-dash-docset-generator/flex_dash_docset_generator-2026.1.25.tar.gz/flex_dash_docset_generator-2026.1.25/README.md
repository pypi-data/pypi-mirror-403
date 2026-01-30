Dash docset generator for [Flex](https://github.com/westes/flex)

### Instructions

- Download and build
[upstream source](https://github.com/westes/flex)
    - Latest release can be found 
    [here](https://github.com/westes/flex/releases/latest)
    - You only need to build the html documentation

- `flex-dash-docset-generator MANUAL_SOURCE`

    - If `pipx` is installed, you can avoid `pip install`ing anything and just
    run `pipx run flex-dash-docset-generator MANUAL_SOURCE`
    - `MANUAL_SOURCE` will be the path to the html sources, which 
    should be something like `flex/doc/flex.html`
    - For a full set of options: `flex-dash-docset-generator -h`
