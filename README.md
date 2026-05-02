**Arya Client V0.0.1**

Arya Loader

**need to do**
setup github
finish paths
complete actual update loop

**how the loader will work**

the updater will auto run from registry
checking the repo and local version
if the repo and local are the same, it won't update; just run main script contents
if the repo is a high ver # then local, then updater will check if the updater needs to be updated
if so, it'll update it self first, and since it has the same file name and path, it'll just autorun
once finished updating it self, the updater will update the rest of the files
then execute