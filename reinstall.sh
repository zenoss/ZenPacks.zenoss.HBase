set -x

zenpack --remove ZenPacks.zenoss.HBase
zenpack --link --install .

zopectl restart
zenhub restart

set +x
