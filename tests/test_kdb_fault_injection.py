import kbuild
import ktest
import pytest
from types import MethodType

def expect_kdb(self):
	'''
	Manage the pager until we get a kdb prompt (or timeout)
	'''
	while True:
		if 0 == self.expect(['kdb>', 'more>']):
			return
		self.send(' ')

def bind_methods(c):
	# TODO: Can we use introspection to find methods to bind?
	c.expect_kdb = MethodType(expect_kdb, c)

@pytest.fixture(scope="module")
def kdb():
	kbuild.config(kgdb=True)
	kbuild.build()

	qemu = ktest.qemu()

	console = qemu.console
	bind_methods(console)
	console.expect_boot()
	console.expect_busybox()

	yield qemu

	qemu.close()

def test_BUG(kdb):
	'''
	Test how kdb reacts to a BUG()
	'''

	# Must use /bin/echo... if we use a shell built-in then the
	# kernel will kill off the shell when we resume
	kdb.console.sendline('/bin/echo BUG > /sys/kernel/debug/provoke-crash/DIRECT')

	kdb.console.expect('Entering kdb')
	# If we timeout here its probably because we've returned to the
	# shell prompt... thankfully that means we don't need any custom
	# error recovery to set us up for the next test!
	kdb.console.expect_kdb()

	kdb.console.send('go\r')
	kdb.console.expect('Catastrophic error detected')
	kdb.console.expect('type go a second time')
	kdb.console.expect_kdb()

	kdb.console.send('go\r')
	kdb.console.expect_prompt()

def test_BUG_again(kdb):
	'''
	Repeat the BUG() test.

	This test effectively ensures there is nothing "sticky" about
	continuing past the catastrophic error (i.e. this is an important
	property for test suite robustness.
	'''
	test_BUG(kdb)

def test_WARNING(kdb):
	'''
	Test how kdb reacts to a WARN_ON()
	'''

	kdb.console.sendline('echo WARNING > /sys/kernel/debug/provoke-crash/DIRECT')
	kdb.console.expect('WARNING')
	kdb.console.expect('lkdtm_WARNING')
	kdb.console.expect_prompt()

