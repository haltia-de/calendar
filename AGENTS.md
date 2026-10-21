# calendar

«Календарь» is the wall calendar of the [Haltia](https://github.com/haltia-de) desktop. It draws a month as a Monday-first grid. Weekends and the Russian public holidays named in the script are red, today is blue, and a tap on the month name shows the year. It only shows dates.

The application id is `io.github.haltia_de.Calendar`. The command and the Alpine package are both `haltia-calendar`. The previous command `b8k-calendar`, and a hidden desktop file for `io.github.trudenboy.Calendar`, remain until version 3.0.

## Layout

- `haltia-calendar` is the program: one Python 3 script, GTK 3 through PyGObject. The id in code is `APP_ID`.
- `data/io.github.haltia_de.Calendar.desktop` is the launcher (`Exec=haltia-calendar`, `X-Haltia-Home=true`).
- `data/io.github.haltia_de.Calendar.svg` is the icon.
- `data/io.github.haltia_de.Calendar.metainfo.xml` is the AppStream record. Each version is a `<release>`.
- `data/io.github.trudenboy.Calendar.desktop` is the hidden launcher of the old id (`NoDisplay=true`).
- `install.sh` installs the program, both desktop files, the icon and the metainfo, and links `b8k-calendar` to `haltia-calendar`.
- `packaging/alpine/APKBUILD` is the noarch Alpine package.
- `NEWS.md` is the release notes, in Russian and in English.
- `.github/workflows/release.yml` runs on a `vX.Y.Z` tag and calls `haltia-de/ci`.
- `LICENSE` is GPL-2.0.

## Run and install

Python 3 with PyGObject (GTK 3) is the only dependency. The script does not load `data/` while it runs. From a checkout:

```sh
python3 haltia-calendar
```

The shebang is `#!/usr/bin/env python3`, so `./haltia-calendar` works when the file is executable.

Install onto a system or into a packaging root:

```sh
sh install.sh [ROOT] [PREFIX]
```

`ROOT` empty, or `/`, means this system. `PREFIX` defaults to `/usr/local`. `packaging/alpine/APKBUILD` calls `sh ./install.sh "$pkgdir" /usr`.

## Release

A release is the tag `vX.Y.Z`. Pushing that tag starts `.github/workflows/release.yml`, which uses `haltia-de/ci/.github/workflows/apk.yml@v1` (`arch: noarch`) to build the signed Alpine package and put it on the GitHub release.

Before the tag, write the notes in `NEWS.md`, set `pkgver` in `packaging/alpine/APKBUILD` to the same `X.Y.Z`, and add that version as a `<release>` in the metainfo, with the notes from `NEWS.md`.

Tag a release, or publish it, only after the user approves that release.

## Conventions

Shared rules for this project live in [docs/conventions.md](https://github.com/haltia-de/haltia/blob/main/docs/conventions.md) in [haltia-de/haltia](https://github.com/haltia-de/haltia) (ADR 0005). Read them there.
