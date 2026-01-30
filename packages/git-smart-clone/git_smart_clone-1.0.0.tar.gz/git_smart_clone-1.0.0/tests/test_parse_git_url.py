from git_smart_clone.smart_clone import parse_git_url


class TestParseGitUrl:
    def test_github_https_url(self):
        url = "https://github.com/sam-phinizy/git-smart-clone"
        result = parse_git_url(url)

        assert result.host == "github.com"
        assert result.owner == "sam-phinizy"
        assert result.repo == "git-smart-clone"

    def test_github_ssh_url(self):
        url = "git@github.com:sam-phinizy/git-smart-clone.git"
        result = parse_git_url(url)

        assert result.host == "github.com"
        assert result.owner == "sam-phinizy"
        assert result.repo == "git-smart-clone"

    def test_gitlab_https_url(self):
        url = "https://gitlab.com/user/project"
        result = parse_git_url(url)

        assert result.host == "gitlab.com"
        assert result.owner == "user"
        assert result.repo == "project"

    def test_gitlab_ssh_url(self):
        url = "git@gitlab.com:user/project.git"
        result = parse_git_url(url)

        assert result.host == "gitlab.com"
        assert result.owner == "user"
        assert result.repo == "project"

    def test_bitbucket_https_url(self):
        url = "https://bitbucket.org/owner/repo"
        result = parse_git_url(url)

        assert result.host == "bitbucket.org"
        assert result.owner == "owner"
        assert result.repo == "repo"

    def test_sourcehut_https_url(self):
        url = "https://git.sr.ht/~user/repo"
        result = parse_git_url(url)

        assert result.host == "git.sr.ht"
        assert result.owner == "user"
        assert result.repo == "repo"

    def test_sourcehut_ssh_url(self):
        url = "git@git.sr.ht:~user/repo"
        result = parse_git_url(url)

        assert result.host == "git.sr.ht"
        assert result.owner == "user"
        assert result.repo == "repo"

    def test_codeberg_https_url(self):
        url = "https://codeberg.org/user/project"
        result = parse_git_url(url)

        assert result.host == "codeberg.org"
        assert result.owner == "user"
        assert result.repo == "project"

    def test_custom_gitea_url(self):
        url = "https://gitea.example.com/org/project"
        result = parse_git_url(url)

        assert result.host == "gitea.example.com"
        assert result.owner == "org"
        assert result.repo == "project"

    def test_url_with_git_extension(self):
        url = "https://github.com/user/repo.git"
        result = parse_git_url(url)

        assert result.repo == "repo"

    def test_git_protocol_url(self):
        url = "git://github.com/user/repo.git"
        result = parse_git_url(url)

        assert result.host == "github.com"
        assert result.owner == "user"
        assert result.repo == "repo"

    def test_self_hosted_gitlab(self):
        url = "https://gitlab.mycompany.com/team/project"
        result = parse_git_url(url)

        assert result.host == "gitlab.mycompany.com"
        assert result.owner == "team"
        assert result.repo == "project"

    def test_ssh_url_without_git_prefix(self):
        url = "github.com:user/repo"
        result = parse_git_url(url)

        assert result.host == "github.com"
        assert result.owner == "user"
        assert result.repo == "repo"
