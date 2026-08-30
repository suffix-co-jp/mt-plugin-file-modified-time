package FileModifiedTime::FileModifiedTime::Tags;

use strict;
use warnings;
use File::Spec ();
use Cwd ();
use POSIX qw(strftime);

sub _normalize_file_arg {
    my ($file) = @_;

    return '' unless defined $file && length $file;

    $file =~ s/^\s+//;
    $file =~ s/\s+$//;

    return '' unless length $file;
    return '' if $file =~ /\0/;
    return '' if $file =~ m{\\};

    # Remove a leading MT URL function tag if it remains unexpanded.
    # Examples:
    #   <mt:SiteURL>...
    #   <mt:WebsiteURL>...
    #   <mt:BlogURL>...
    #   <mt:SiteRelativeURL>...
    #   <$mt:WebsiteURL$>...
    #
    # Generic rule: leading MT function-tag name ending in "URL".
    $file =~ s{
        \A
        <\s*
        \$?
        mt:
        [A-Za-z][A-Za-z0-9_]*URL
        \$?
        \s*
        >
    }{}ix;

    # Normalize already-expanded absolute/protocol-relative URLs to path only.
    if ( $file =~ m{\Ahttps?://}i ) {
        $file =~ s{\Ahttps?://[^/]+}{}i;
    }
    elsif ( $file =~ m{\A//} ) {
        $file =~ s{\A//[^/]+}{};
    }

    # Query strings and fragments are not part of the filesystem path.
    $file =~ s/[?#].*\z//s;

    # Reject parent traversal.
    return '' if $file =~ m{(?:^|/)\.\.(?:/|$)};

    # Resolve all accepted forms below the current site's site_path.
    $file =~ s{^/+}{};
    $file =~ s{^\./+}{};

    return $file;
}

sub _format_mtime {
    my ( $mtime, $format ) = @_;

    # Default: YYYYMMDDHHMMSS
    return strftime( '%Y%m%d%H%M%S', localtime($mtime) )
        unless defined $format && length $format;

    # Explicit Unix timestamp mode.
    return $mtime if lc($format) eq 'unix';

    # Optional custom strftime format.
    return strftime( $format, localtime($mtime) );
}

# Verify that $path, once symlinks/.. are fully resolved, still lives
# under the resolved site_path. Defends against symlink escapes that the
# textual "../" check cannot catch.
sub _is_within_site_path {
    my ( $path, $site_path ) = @_;

    my $real_base = Cwd::realpath($site_path);
    return 0 unless defined $real_base && length $real_base;

    my $real_path = Cwd::realpath($path);
    return 0 unless defined $real_path && length $real_path;

    # Normalize trailing slash on the base, then require a path-boundary match.
    $real_base =~ s{/+$}{};

    return 1 if $real_path eq $real_base;
    return 1 if index( $real_path, $real_base . '/' ) == 0;
    return 0;
}

sub file_modified_time {
    my ( $ctx, $args ) = @_;

    my $file = _normalize_file_arg( $args->{file} );
    return '' unless length $file;

    my $site = $ctx->stash('blog');
    return '' unless $site;

    my $site_path = $site->site_path;
    return '' unless defined $site_path && length $site_path;

    my @parts = grep { length $_ && $_ ne '.' } split m{/+}, $file;
    return '' unless @parts;

    my $path = File::Spec->catfile( $site_path, @parts );
    return '' unless -f $path;

    # Ensure the resolved real path stays under the site's real path,
    # even in the presence of symbolic links.
    return '' unless _is_within_site_path( $path, $site_path );

    my $mtime = ( stat($path) )[9];
    return '' unless defined $mtime;

    return _format_mtime( $mtime, $args->{format} );
}

1;
