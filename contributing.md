### Contributing to vimiv

---
> :construction: **NOTE:** The future of vimiv is in the
> [Qt port](https://github.com/karlch/vimiv-qt) as discussed in
> [this issue](https://github.com/karlch/vimiv/issues/61). New features will only be
> implemented there and many improvements have already been made. Sticking with this
> deprecated version is only recommended if you require a more stable software. In case
> you miss anything in the Qt port, please
> [open an issue](https://github.com/karlch/vimiv-qt/issues). Check the
> [roadmap](https://karlch.github.io/vimiv-qt/roadmap.html) for more details.
---

Therefore, if you wish to implement a new feature, please consider doing this in the
[Qt port](https://github.com/karlch/vimiv-qt). You can find some general information
[on its website](https://karlch.github.io/vimiv-qt/)
as well as some helpful
[starting points for contributing there](https://karlch.github.io/vimiv-qt/documentation/contributing.html).

### Reporting bugs
If possible, please reproduce the bug running with --debug and include the
content of the created logfile in $XDG_DATA_HOME/vimiv/vimiv.log.

Vimiv tries to maintain backward compatibility with the latest Ubuntu LTS
version. Supporting older systems is not planned and things will almost
certainly break on them.
