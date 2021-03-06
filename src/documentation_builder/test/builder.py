"""Test module for builder.py."""

import sys
import os
import shutil
import filecmp
from tempfile import mkdtemp
from unittest import TestCase, main, TestLoader
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../lib')))  # noqa
from quattordocbuild import builder


class BuilderTest(TestCase):
    """Test class for builder.py."""

    def setUp(self):
        """Set up temp dir for tests."""
        self.tmpdir = mkdtemp()

    def tearDown(self):
        """Remove temp dir."""
        shutil.rmtree(self.tmpdir)

    def test_which(self):
        """Test which function."""
        self.assertFalse(builder.which('testtest1234'))
        self.assertTrue(builder.which('python'))

    def test_check_input(self):
        """Test check_input function."""
        self.assertFalse(builder.check_input("", ""))
        self.assertFalse(builder.check_input(self.tmpdir, ""))
        self.assertFalse(builder.check_input("/nonexistingdir", ""))
        self.assertTrue(builder.check_input(self.tmpdir, self.tmpdir))
        os.makedirs(os.path.join(self.tmpdir, "test"))
        self.assertTrue(builder.check_input(self.tmpdir, os.path.join(self.tmpdir, "test")))

    def test_check_commands(self):
        """Test check_commands function."""
        self.assertTrue(builder.check_commands(True))

    def test_build_site_structure(self):
        """Test build_site_structure function."""
        repomap = {
            "configuration-modules-core": {
                "sitesection": "components",
                "targets": ["/NCM/Component/", "/components/", "/pan/quattor/"]
            },
            "CCM": {
                "sitesection": "CCM",
                "targets": ["EDG/WP4/CCM/"],
            },
        }
        testdata = {'CCM': {'/tmp/qdoc/src/CCM/target/doc/pod/EDG/WP4/CCM/Fetch/Download.pod':
                            "# NAME\n\nEDG::WP4::CC"},
                    'configuration-modules-core':
                    {'/tmp/doc/src/configuration-modules-core/ncm-profile/target/pan/components/profile/functions.pan':
                     u'\n### Functions\n',
                     '/tmp/doc/src/configuration-modules-core/ncm-fmonagent/target/doc/pod/NCM/Component/fmonagent.pod':
                     'Hello',
                     '/tmp/doc/src/configuration-modules-core/ncm-freeipa/target/pan/quattor/aii/freeipa/schema.pan':
                     'Hello2'
                     }}
        expected_response = {'CCM': {'Fetch::Download.md': '# NAME\n\nEDG::WP4::CC'},
                             'components': {'aii::freeipa::schema.md': 'Hello2',
                                            'fmonagent.md': 'Hello',
                                            'profile::functions.md': u'\n### Functions\n'}}
        self.assertEquals(builder.build_site_structure(testdata, repomap), expected_response)

    def test_make_interlinks(self):
        """Test make_interlinks function."""
        # Replace one reference
        test_data = {'components-grid': {'fmonagent.md': ''},
                     'components': {'icinga.md': 'I refer to `fmonagent`.'}}
        expected = {'components-grid': {'fmonagent.md': ''},
                    'components': {'icinga.md': 'I refer to [fmonagent](../components-grid/fmonagent.md).'}}
        self.assertEquals(builder.make_interlinks(test_data), expected)

        # Replace two references
        test_data = {'comps-gr': {'fmnt.md': ''},
                     'comps': {'icinga.md': 'refr `fmnt` and `fmnt`.'}}
        expected = {'comps-gr': {'fmnt.md': ''},
                    'comps': {'icinga.md': 'refr [fmnt](../comps-gr/fmnt.md) and [fmnt](../comps-gr/fmnt.md).'}}
        self.assertEquals(builder.make_interlinks(test_data), expected)

        # Replace ncm- reference
        test_data = {'components-grid': {'fmonagent.md': ''},
                     'components': {'icinga.md': 'I refer to `ncm-fmonagent`.'}}
        expected = {'components-grid': {'fmonagent.md': ''},
                    'components': {'icinga.md': 'I refer to [fmonagent](../components-grid/fmonagent.md).'}}
        self.assertEquals(builder.make_interlinks(test_data), expected)

        # Replace newline reference
        test_data = {'components-grid': {'fmonagent.md': ''},
                     'components': {'icinga.md': 'I refer to \n`ncm-fmonagent`.'}}
        expected = {'components-grid': {'fmonagent.md': ''},
                    'components': {'icinga.md': 'I refer to \n[fmonagent](../components-grid/fmonagent.md).'}}
        self.assertEquals(builder.make_interlinks(test_data), expected)

        # Replace linked wrong reference
        test_data = {'components-grid': {'fmonagent.md': ''},
                     'components': {'icinga.md': 'I refer \
to [NCM::Component::FreeIPA::Client](https://metacpan.org/pod/NCM::Component::FreeIPA::Client).',
                                    'FreeIPA::Client': 'Allo'}}
        expected = {'components-grid': {'fmonagent.md': ''},
                    'components': {'icinga.md': 'I refer to [FreeIPA::Client](../components/FreeIPA::Client).',
                                   'FreeIPA::Client': 'Allo'}}

        self.assertEquals(builder.make_interlinks(test_data), expected)

        # Don't replace in own page
        test_data = {'comps-grid': {'fmonagent.md': 'ref to `fmonagent`.'},
                     'comps': {'icinga.md': 'ref to `icinga` and `ncm-icinga`.'}}
        self.assertEquals(builder.make_interlinks(test_data), test_data)

    def test_write_site(self):
        """Test write_site function."""
        input = {'CCM': {'fetch::download.md': '# NAME\n\nEDG::WP4::CC'},
                 'components': {'fmonagent.md': 'Hello',
                                'profile::functions.md': u'\n### Functions\n'}}

        sitedir = os.path.join(self.tmpdir, "docs")
        builder.write_site(input, self.tmpdir, "docs")
        self.assertTrue(os.path.exists(os.path.join(sitedir, 'components')))
        self.assertTrue(os.path.exists(os.path.join(sitedir, 'components/profile::functions.md')))
        self.assertTrue(os.path.exists(os.path.join(sitedir, 'components/fmonagent.md')))
        self.assertTrue(os.path.exists(os.path.join(sitedir, 'CCM')))
        self.assertTrue(os.path.exists(os.path.join(sitedir, 'CCM/fetch::download.md')))

    def test_write_toc(self):
        """Test write_toc function."""
        toc = {'CCM': set(['fetch::download.md']), 'components': set(['fmonagent.md', 'profile::functions.md'])}
        builder.write_toc(toc, self.tmpdir)
        with open(os.path.join(self.tmpdir, "mkdocs.yml")) as fih:
            print fih.read()
        self.assertTrue(filecmp.cmp('test/testdata/mkdocs.yml', os.path.join(self.tmpdir, "mkdocs.yml")))

        toc = {'components': set(['profile::functions.md', 'fmonagent.md']), 'CCM': set(['fetch::download.md'])}
        builder.write_toc(toc, self.tmpdir)
        with open(os.path.join(self.tmpdir, "mkdocs.yml")) as fih:
            print fih.read()
        self.assertTrue(filecmp.cmp('test/testdata/mkdocs.yml', os.path.join(self.tmpdir, "mkdocs.yml")))

    def suite(self):
        """Return all the testcases in this module."""
        return TestLoader().loadTestsFromTestCase(BuilderTest)

if __name__ == '__main__':
    main()
