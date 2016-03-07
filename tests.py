# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import unittest
from datetime import datetime
from unittest import TestCase
from mock import patch, Mock
from click.testing import CliRunner
from statuspage import cli, update, create, iter_systems, get_severity, SYSTEM_LABEL_COLOR
from github import UnknownObjectException


class CLITestCase(TestCase):

    @patch("statuspage.run_update")
    @patch("statuspage.Github")
    def test_create(self, GithubMock, run_update):

        gh = Mock()
        GithubMock.return_value = gh

        label = Mock()
        gh.get_user().create_repo().get_labels.return_value = [label,]

        runner = CliRunner()
        result = runner.invoke(
                create,
                ["--name", "testrepo", "--token", "token", "--systems", "sys1,sys2"]
        )

        self.assertEqual(result.exit_code, 0)

        GithubMock.assert_called_once_with("token")


    @patch("statuspage.Github")
    def test_update(self, GithubMock):

        gh = Mock()
        GithubMock.return_value = gh

        # setup mocked label
        label = Mock()
        label.color = "171717"
        label.name = "Website"

        label1 = Mock()
        label1.color = "171717"
        label1.name = "API"

        gh.get_user().get_repo().get_labels.return_value = [label, label1]

        # set up mocked issue
        issue = Mock()
        issue.created_at = datetime.now()
        issue.state = "open"
        issue_label = Mock()
        issue_label.color = "FF4D4D"
        issue_label.name = "major outage"
        issue.get_labels.return_value = [issue_label, label]
        comment = Mock()
        issue.get_comments.return_value = [comment, ]

        issue1 = Mock()
        issue1.created_at = datetime.now()
        issue1.state = "open"
        issue1.get_labels.return_value = [issue_label, label1]
        issue1.get_comments.return_value = [comment, ]

        gh.get_user().get_repo().get_issues.return_value = [issue, issue1]
        template = Mock()
        template.decoded_content = b"some foo"
        gh.get_user().get_repo().get_file_contents.return_value = template

        runner = CliRunner()
        result = runner.invoke(update, ["--name", "testrepo", "--token", "token"])
        self.assertEqual(result.exit_code, 0)
        GithubMock.assert_called_with("token")

        gh.get_user().get_repo.assert_called_with(name="testrepo")
        gh.get_user().get_repo().get_labels.assert_called_once_with()

    @patch("statuspage.Github")
    def test_update_index_does_not_exist(self, GithubMock):

        gh = Mock()
        GithubMock.return_value = gh

        # setup mocked label
        label = Mock()
        label.color = "171717"
        label.name = "Website"
        gh.get_user().get_repo().get_labels.return_value = [label, ]

        # set up mocked issue
        issue = Mock()
        issue.state = "open"
        issue_label = Mock()
        issue_label.color = "FF4D4D"
        issue_label.name = "major outage"
        issue.get_labels.return_value = [issue_label, label]
        comment = Mock()
        issue.get_comments.return_value = [comment, ]
        gh.get_user().get_repo().get_issues.return_value = [issue, ]
        template = Mock()
        template.decoded_content = b"some foo"
        gh.get_user().get_repo().get_file_contents.return_value = template
        gh.get_user().get_repo().update_file.side_effect = UnknownObjectException(status=404, data="foo")

        runner = CliRunner()
        result = runner.invoke(update, ["--name", "testrepo", "--token", "token"])
        self.assertEqual(result.exit_code, 0)

        GithubMock.assert_called_with("token")

        gh.get_user().get_repo.assert_called_with(name="testrepo")
        gh.get_user().get_repo().get_labels.assert_called_once_with()
        gh.get_user().get_repo().create_file.assert_called_once_with(
            branch='gh-pages',
            content='some foo',
            message='initial',
            path='/index.html'
        )


class UtilTestCase(TestCase):

    def test_iter_systems(self):
        label1 = Mock()
        label2 = Mock()
        label1.name = "website"
        label1.color = SYSTEM_LABEL_COLOR

        self.assertEqual(
            list(iter_systems([label1, label2])),
            ["website", ]
        )

        self.assertEqual(
            list(iter_systems([label2])),
            []
        )

    def test_severity(self):
        label1 = Mock()
        label2 = Mock()
        label1.color = "FF4D4D"

        self.assertEqual(
            get_severity([label1, label2]),
            "major outage"
        )

        label1.color = "000000"

        self.assertEqual(
            get_severity([label1, label2]),
            None
        )




if __name__ == '__main__':
    unittest.main()