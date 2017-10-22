import os
import traceback
import sys

def run(cmd, failmsg=None):
	'''Run a command (synchronously) raising an exception on
	failure.

	'''

	# Automatically manage bisect skipping
	if failmsg:
		try:
			run(cmd)
			return
		except:
			skip(failmsg)

	print('+ ' + cmd)
	(exit_code) = os.system(cmd)
	if exit_code != 0:
		raise Exception

def skip(msg):
	"""Report a catastrophic build error.
        
        A catastrophic build error occurs when we cannot build the software
        under test. This makes testing of any form impossible. We treat this
        specially (and completely out of keeping with pytest philosophy because
        it allows us to return a special error code that will cause git bisect
        to look for a kernel we can compile.
        """
	traceback.print_exc()
	print('### SKIP: %s ###' % (msg,))
	sys.exit(125)

def config(kgdb=False):
	need_olddefconfig=kgdb

	# HACK: Still trying to come up with a nice way to handle the two
	#       directories involved (kernel and kcontest). For now we'll
	#       just hack things and rely on the Makefile to set up the
	#       environment variables we need.
	os.chdir(os.environ['KERNEL_DIR'])

	run('make defconfig',
		'Cannot configure kernel (wrong directory)')

	if kgdb:
		run('scripts/config ' +
			'--enable DEBUG_INFO ' +
			'--enable MAGIC_SYSRQ ' +
			'--enable KGDB --enable KGDB_KDB --enable KDB_KEYBOARD',
			'Cannot configure kgdb extensions')
		
	if need_olddefconfig:
		run('make olddefconfig',
			'Cannot finalize kernel configuration')

def build():
	run('make -j `nproc` all modules_install ' +
		'INSTALL_MOD_PATH=$PWD/mod-rootfs INSTALL_MOD_STRIP=1',
		'Cannot compile kernel')

	run('unxz -c $KCONTEST_DIR/buildroot/x86/rootfs.cpio.xz > rootfs.cpio',
		'Cannot decompress rootfs')
	run('(cd mod-rootfs; find . | cpio -H newc -AoF ../rootfs.cpio)',
		'Cannot copy kernel modules into rootfs')
	# Compressing with xz would be expensive, gzip is enough here
	run('pwd; gzip -f rootfs.cpio',
		'Cannot recompress rootfs')

