# Copyright (c) 2004-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

import logging
import os

from clusterondemand.cidr import cidr, cidr_list
from clusterondemand.clusternameprefix import must_start_with_cod_prefix
from clusterondemand.configuration_validation import (
    generate_password_if_not_set,
    validate_access_to_cluster,
    validate_password_strength
)
from clusterondemand.inbound_traffic_rule import InboundTrafficRule
from clusterondemand.ip import ip, ip_must_be_within_cidr, nth_ip_in_default_network
from clusterondemand.versioned_product_key import VersionedProductKey, validate_product_key_list
from clusterondemandconfig import (
    ConfigNamespace,
    files_and_urls_accessible,
    if_set_file_exists_and_readable,
    match_http_proxy_format,
    may_not_equal_none,
    must_be_valid_timezone,
    require_at_least_one_to_be_set,
    requires_at_least_one_other_parameter,
    requires_other_parameter_to_be_set
)

from . import localpath
from .clusternameprefix import clusterprefix_ns
from .paramvalidation import warn_user_about_cluster_name_length
from .utils import confirm_ns

log = logging.getLogger("cluster-on-demand")

ENFORCING_CONFIG_FILES = [
    "/etc/cm-cluster-on-demand.d/enforced.ini"
]

SYSTEM_CONFIG_FILES = [
    "/etc/cm-cluster-on-demand.ini",
    "/etc/cm-cluster-on-demand.conf",
    "/etc/cm-cluster-on-demand.d/*",
]
USER_CONFIG_FILES = [
    os.path.expanduser("~/cm-cluster-on-demand.ini"),
    os.path.expanduser("~/cm-cluster-on-demand.conf"),
    os.path.expanduser("~/cm-cluster-on-demand.d/*.ini"),
    os.path.expanduser("~/cm-cluster-on-demand.d/*.conf"),
    os.path.expanduser("~/.cm-cluster-on-demand.ini"),
    os.path.expanduser("~/.cm-cluster-on-demand.conf"),
    os.path.expanduser("~/.config/cm-cluster-on-demand/*.ini"),
    os.path.expanduser("~/.config/cm-cluster-on-demand/*.conf")
]

NO_WLM = "dont-configure"

WLMS_8_2 = [
    NO_WLM,
    "slurm",
    "sge",
    "pbspro",
    "pbspro-ce",
    "openpbs",
    # LSF and UGE are supported by Bright, but not ouf of the box
]

ALL_WLMS = list(set(WLMS_8_2))

DEFAULT_DISK_SETUP = """
<?xml version='1.0' encoding='ISO-8859-1'?>
<!-- This is the CoD default -->
<!-- Just a single xfs partition -->
<diskSetup xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance'>
  <device>
    <blockdev>/dev/vdb</blockdev>
    <blockdev>/dev/sda</blockdev>
    <blockdev>/dev/nvme0n1</blockdev>
    <blockdev mode='cloud'>/dev/sdb</blockdev>
    <blockdev mode='cloud'>/dev/hdb</blockdev>
    <blockdev mode='cloud'>/dev/vdb</blockdev>
    <blockdev mode='cloud'>/dev/xvdb</blockdev>
    <blockdev mode='cloud'>/dev/xvdf</blockdev>
    <blockdev mode='cloud'>/dev/nvme1n1</blockdev>
    <partition id='a2'>
      <size>max</size>
      <type>linux</type>
      <filesystem>xfs</filesystem>
      <mountPoint>/</mountPoint>
      <mountOptions>defaults,noatime,nodiratime</mountOptions>
    </partition>
  </device>
</diskSetup>
"""

OS_DEFAULT_NODE_DISK_SETUP_11_AND_ABOVE = """
<?xml version="1.0" encoding="UTF-8"?>
<diskSetup>
  <device>
    <blockdev>/dev/vdb</blockdev>
    <blockdev>/dev/sda</blockdev>
    <blockdev>/dev/nvme0n1</blockdev>
    <blockdev mode="cloud">/dev/sdb</blockdev>
    <blockdev mode="cloud">/dev/hdb</blockdev>
    <blockdev mode="cloud">/dev/vdb</blockdev>
    <blockdev mode="cloud">/dev/xvdf</blockdev>
    <partitionTable>gpt</partitionTable>
    <partition id="a0" partitiontype="bios_grub">
      <size>1M</size>
      <type>linux</type>
    </partition>

    <partition id="a1" partitiontype="esp">
      <size>265M</size>
      <type>linux</type>
      <filesystem>fat</filesystem>
      <mountPoint>/boot/efi</mountPoint>
      <mountOptions>defaults,noatime,nodiratime</mountOptions>
    </partition>

    <partition id="a2">
      <size>max</size>
      <type>linux</type>
      <filesystem>xfs</filesystem>
      <mountPoint>/</mountPoint>
      <mountOptions>defaults,noatime,nodiratime</mountOptions>
    </partition>
  </device>
</diskSetup>
"""

DEFAULT_DISK_SETUP_10_AND_ABOVE = """
<?xml version='1.0' encoding='ISO-8859-1'?>
<!-- This is the CoD default -->
<!-- Just a single xfs partition -->
<diskSetup xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance'>
  <device>
    <blockdev>/dev/vdb</blockdev>
    <blockdev>/dev/sda</blockdev>
    <blockdev>/dev/nvme0n1</blockdev>
    <blockdev mode='cloud'>/dev/sdb</blockdev>
    <blockdev mode='cloud'>/dev/hdb</blockdev>
    <blockdev mode='cloud'>/dev/vdb</blockdev>
    <blockdev mode='cloud'>/dev/xvdf</blockdev>
    <partition id='a2'>
      <size>max</size>
      <type>linux</type>
      <filesystem>xfs</filesystem>
      <mountPoint>/</mountPoint>
      <mountOptions>defaults,noatime,nodiratime</mountOptions>
    </partition>
  </device>
</diskSetup>
"""

configuration_ns = ConfigNamespace("configuration.output", "configuration parameters")
# TODO: move namespace with system_config and config parameters to cod-config.
#  They are used by cod-config and should be defined there.
configuration_ns.add_switch_parameter(
    "show_configuration",
    advanced=True,
    help="Show configuration before actual command execution")
configuration_ns.add_switch_parameter(
    "show_secrets",
    advanced=True,
    help=("When dumping the configuration, it should show the values of secret parameters, "
          "e.g. passwords, keys, etc."))
configuration_ns.add_switch_parameter(
    "check_config",
    advanced=True,
    default=True,
    help="Check configuration doesn't have unknown sections and parameters.")
configuration_ns.add_switch_parameter(
    "check_config_for_all_commands",
    advanced=True,
    default=False,
    help=("Check configuration for all known COD-commands. By default, only config sections"
          " related to current command are checked. This makes config check much slower"))
configuration_ns.add_switch_parameter(
    "system_config",
    advanced=True,
    boot=True,
    default=True,
    help="Load system config files implicitly. If disabled, only config files specified with --config are loaded")
configuration_ns.add_enumeration_parameter(
    "config",
    boot=True,
    default=None,
    flags=["-c"],
    help="Extra config files")

eula_ns = ConfigNamespace("common.eula", help_section="eula parameters")
eula_ns.add_switch_parameter(
    "accept_eula",
    advanced=True,
    help="Accept the most recent EULA and skip the dialog")
eula_ns.add_switch_parameter(
    "show_eula",
    advanced=True,
    default=False,
    help="Display the contents of EULA")
eula_ns.add_parameter(
    "user_accepted_eula_file",
    advanced=True,
    default=os.path.expanduser("~/.cm-cod-accepted-eula"),
    help="The file location where the EULA accepted by the user is saved.",
    parser=os.path.expanduser,
    validation=may_not_equal_none)


events_ns = ConfigNamespace("common.events", help_section="event settings")
events_ns.add_switch_parameter(
    "events",
    advanced=True,
    help="Make the cod client send JSON HTTP events to "
         "the URL specified with --events-url . Events report which 'cod' sub "
         "commands are being used and in what way.")
events_ns.add_parameter(
    "events_url",
    advanced=True,
    help="HTTP URL to which the events are sent, e.g. http://example:12345")
events_ns.add_parameter(
    "events_timeout",
    advanced=True,
    default=1,
    help_varname="SECONDS",
    help="Max time in seconds to try to connect and submit the event. Timeouts are not fatal.")
events_ns.add_switch_parameter(
    "events_in_ve",
    advanced=True,
    default=False,
    validation=requires_other_parameter_to_be_set("events"),
    help="Send events to the event URL even when executing inside of a Python virtual environment")


common_ns = ConfigNamespace("common", help_section="common parameters")
common_ns.import_namespace(configuration_ns)
common_ns.import_namespace(eula_ns)
common_ns.import_namespace(events_ns)
common_ns.add_switch_parameter(
    "help",
    flags=["-h"],
    help="Show this message and exit")
common_ns.add_switch_parameter(
    "advanced_help",
    flags=["-H"],
    help="Don't omit advanced configuration parameters from the help output. Implies --help")
common_ns.add_parameter(
    "explain",
    help=(
        "Show detailed information about the immediately following parameter."
        " Which can be a name, a regular expression, ENV VAR or another flag."
    ))
common_ns.add_switch_parameter(
    "verbose",
    flags=["-v", "-vv", "-vvv"],
    help="Verbosity level")
common_ns.add_switch_parameter(
    "print_stack_trace_on_failure",
    default=False,
    help="Print the stack trace on failure, even if -v wasn't specified")
common_ns.add_parameter(
    "log_file",
    advanced=True,
    help="File to write full debug log to",
    parser=os.path.expanduser)
common_ns.add_switch_parameter(
    "log_omit_time",
    advanced=True,
    help="Omit timestamp information in console log")
common_ns.add_switch_parameter(
    "pdb_on_error",
    advanced=True,
    help="Run PDB post mortem on error")
common_ns.add_switch_parameter(
    "only_ascii_arguments",
    default=True,
    advanced=True,
    help="Only allow for ASCII characters to be used in CLI arguments. "
         "Useful when pasting values from user interfaces which might contain invisible non-ASCII "
         "characters.")
common_ns.add_parameter(
    "max_threads",
    default=10,
    advanced=True,
    help="Maximum number of threads for parallel operations."
)
common_ns.add_switch_parameter(
    "version",
    help="Displays version information about cluster-on-demand.",
)


clustercreatelicense_ns = ConfigNamespace(
    "cluster.create.license",
    help_section="Base Command Manager licensing information")
clustercreatelicense_ns.add_parameter(
    "license_unit",
    help="License unit")
clustercreatelicense_ns.add_parameter(
    "license_locality",
    help="License locality")
clustercreatelicense_ns.add_parameter(
    "license_country",
    default="US",
    help="Two characters",
    validation=may_not_equal_none)
clustercreatelicense_ns.add_enumeration_parameter(
    "license_product_key",
    env="LICENSE_PRODUCT_KEY",
    help=("List of multiple BCM product keys. Can contain several product keys with a version specifier prefix. There "
          "can be one key without a version. For example, to use 'key1' for all clusters running a version older then "
          "11.0, and 'key2' for newer versions, use: '<11.0:key1', 'key2' (Replace 'key1'/'key2' with a valid product "
          "key.) Comparison operators can be <, <=, >, >=. The comparison operator can be omitted. For example "
          "'10.0:key3' will use 'key3' when the version is '10.0'. Keys are tested in the order specified. For most "
          "users, specifying a single key without any version prefix will do."),
    secret=True,
    type=[VersionedProductKey],
    validation=[may_not_equal_none, validate_product_key_list])
clustercreatelicense_ns.add_parameter(
    "license_organization",
    help="Name of your organization")
clustercreatelicense_ns.add_parameter(
    "license_state",
    help="Name of your state or province")
clustercreatelicense_ns.add_parameter(
    "license_activation_token",
    env="LICENSE_ACTIVATION_TOKEN",
    advanced=True,
    help="Base Command Manager license activation token. It can be used instead of a product "
         "key. If both are specified, activation token will take precedence (the product key, "
         "if also specified, will be ignored).",
    secret=True)
clustercreatelicense_ns.add_parameter(
    "license_activation_url",
    env="LICENSE_ACTIVATION_URL",
    advanced=True,
    help="Base Command Manager license activation URL. "
         "It should point to a server which is capable of issuing Bright licences after being given "
         "the License Activation Token as input. "
         "Only makes sense if license_activation_token is specified.")
clustercreatelicense_ns.add_parameter(
    "license_activation_password",
    env="LICENSE_ACTIVATION_PASSWORD",
    advanced=True,
    help="Base Command Manager license activation password. "
         "It will be used by cm-bright-setup for client authentication with the license activation server.",
    secret=True)
clustercreatelicense_ns.add_parameter(
    "http_proxy",
    advanced=True,
    default=None,
    help="HTTP proxy to be used on the headnode for contacting the Base Command Manager licensing server.",
    validation=match_http_proxy_format
)


clustercreatepassword_ns = ConfigNamespace(
    "cluster.create.password",
    help_section="root login method to the head node")
clustercreatepassword_ns.add_switch_parameter(
    "log_cluster_password",
    help="Log cluster password to the screen and log files. This option is mandatory if no custom "
         "password, nor SSH keypairs, were specified.")
clustercreatepassword_ns.add_parameter(
    "cluster_password",
    help="The root user password to the cluster. If not specified, a random one will be generated "
         "(use --log-cluster-password to see it). This is also the root user SQL password on the "
         "head node. Upon cluster creation the password is stored in the "
         "/cm/local/apps/cmd/etc/cmd.conf on the head node.",
    secret=True,
    validation=[validate_password_strength, generate_password_if_not_set])
clustercreatepassword_ns.add_parameter(
    "ssh_password_authentication",
    type=bool,
    default=False,
    help="If set to true, it will be possible to SSH to the head node using a "
         "password. This option should NOT be used in untrusted environments as it exposes "
         "the head node to brute force login attacks.")
clustercreatepassword_ns.add_switch_parameter(
    "access_validation",
    default=True,
    help="Causes the cluster creation process to abort early if it won't be able to "
         "guarantee that the SSH access to the cluster will be possible. "
         "Disabling it is useful when e.g. the public SSH key is being delivered to the image in some other "
         "way, than the usual command line argument. "
         "Note, that access validation does not attempt to actually connect to the cluster. "
         "Instead, it merely tries to predict whether the cluster will be accessible to the user, "
         "given the specified argument combination.")
clustercreatepassword_ns.add_parameter(
    "weak_password_policy",
    advanced=True,
    choices=["allow", "warn", "fail"],
    default="warn",
    help="Determine the behavior of cluster create upon the detection of a weak password, when SSH password access "
         "is enabled. When set to 'allow', a weak password will silently be accepted; setting it to 'warn' "
         "triggers printing a warning to the user when a weak password is detected; setting it to 'fail' causes the "
         "cluster creation to abort when a weak password is detected")
clustercreatepassword_ns.add_parameter(
    "ssh_pub_key_path",
    help="Path to an SSH public key file. The key will be added to the authorized keys on the cluster. And the tool "
         "will use the corresponding private key to access the cluster.",
    help_varname="PATH_TO_FILE",
    parser=localpath.localpath,
    validation=[localpath.must_exist, localpath.must_be_readable])
clustercreatepassword_ns.add_validation(validate_access_to_cluster)
clustercreatepassword_ns.add_enumeration_parameter(
    "authorized_key_path",
    advanced=True,
    default=[],
    help_varname="PATH",
    help=("Path or HTTP(S) URL to SSH public key which will be added to authorized keys. Can be specified multiple "
          "times. Unlike --ssh-pub-key-path the tool does not require access to the corresponding private key and "
          "will not use the key to access the cluster. Can be used to authorize additional keys."),
    validation=files_and_urls_accessible,
)
clustercreatepassword_ns.add_switch_parameter(
    "configure_default_image_authorized_keys",
    advanced=True,
    default=False,
    help=("Configure SSH access keys for the default software image. This enables passwordless login to compute nodes "
          "immediately after they're powered on, without requiring additional setup. Must be used with either "
          "--ssh-pub-key-path or --authorized-key-path to specify which keys to add."),
    validation=requires_at_least_one_other_parameter(["authorized_key_path", "ssh_pub_key_path"]),
)

clustercreatewlm_ns = ConfigNamespace("cluster.create.wlm")
clustercreatewlm_ns.add_parameter(
    "wlm",
    choices=ALL_WLMS,
    default=NO_WLM,
    help="Workload Manager of choice. "
         "This can also be configured later. "
         "Note that this list is a subset of the WLM systems supported across different versions of Base "
         "Command Manager. Therefore, some WLM systems are only configurable later on, after the cluster "
         "has been created. Defaults to 'dont-configure'. ",
    help_choices={NO_WLM: "do not configure any (can be configured later)"})


clustercreateconfirm_ns = ConfigNamespace("cluster.create.confirm")
clustercreateconfirm_ns.import_namespace(confirm_ns)
clustercreateconfirm_ns.add_parameter(
    "ask_to_confirm_cluster_creation",
    default=True,
    help="Ask for confirmation when creating a new cluster. Use -y to skip this question.")


clustercreatedisks_ns = ConfigNamespace("cluster.create.disks")
clustercreatedisks_ns.add_parameter(
    "head_node_root_volume_size",
    default=50,
    help="Head node root disk size in GB",
    help_varname="SIZE_IN_GB",
    type=int)

nodes_ns = ConfigNamespace("cluster.create.nodes")
nodes_ns.add_parameter(
    "nodes",
    default=5,
    flags=["-n"],
    help="The amount of cloud nodes to configure for a cluster. "
    "The nodes are not powered on automatically.",
    type=int)

clustercreatename_ns = ConfigNamespace("cluster.create.name")
clustercreatename_ns.add_parameter(
    "name",
    help=("(default: auto) Name of the cluster to create. "
          "By default the name is generated from version, distro and creation timestamp."),
    validation=must_start_with_cod_prefix
)
clustercreatename_ns.add_switch_parameter(
    "validate_max_cluster_name_length",
    default=True,
    advanced=True,
    validation=warn_user_about_cluster_name_length,
    help=("By default, validates cluster name length, to not create cluster with longer than 46 character names. "
          "Overly long names can lead to certificate generation failure or various other issues."),
)

bright_setup_ns = ConfigNamespace("cluster.brightsetup")
bright_setup_ns.add_enumeration_parameter(
    "prebs",
    default=[],
    help_varname="COMMAND",
    help=("Command(s) executed by cloud-init before "
          "cm-bright-setup (before CMDaemon starts). Useful for package update."
          " Multiple arguments are allowed")
)
bright_setup_ns.add_enumeration_parameter(
    "postbs",
    default=[],
    help_varname="COMMAND",
    help="Command(s) executed by cloud-init post cm-bright-setup (Once CMDaemon starts)"
)
bright_setup_ns.add_parameter(
    "run_cm_bright_setup",
    default=True,
    help=("Whether or not to initialize the cluster by running cm-bright-setup "
          "(activate license, etc)"),
)
CFG_NO_ADMIN_EMAIL = "none"
CFG_AUTO_ADMIN_EMAIL = "auto"
bright_setup_ns.add_parameter(
    "admin_email",
    default=CFG_NO_ADMIN_EMAIL,
    help="Admin email address to set in CMDaemon."
)
bright_setup_ns.add_enumeration_parameter(
    "healthchecks_to_disable",
    help=(
        "Some clouds or environments are configured in a way that prevents certain healthchecks from running. "
        "For example, if a user deploys a cluster in a networking environment with disabled ICMP, "
        "the 'defaultgateway' healthcheck, which depends on ping, will always fail. "
        "To avoid this, users may specify a list of healthchecks to disable. "
        "Example: --healthchecks-to-disable defaultgateway ldap"
    ),
)

inbound_rule_ns = ConfigNamespace("cluster.create.inbound_rule")
inbound_rule_ns.add_enumeration_parameter(
    "inbound_rule",
    help=("One or several inbound traffic rules for the cluster's head node in the following format: "
          "[src_cidr[:src_port],]dst_port[:protocol], where port can be a single port or a dash separated range and "
          "supported protocols are: tcp, udp. A wildcard value will be assumed for every optional non-provided "
          "parameter (e.g. all ports, all protocols, all IPs). Note: a special variable '{CLIENT_IP}' can be used to "
          "substitute src_cidr, in which case the COD client's public IP will be detected and used. "
          "Examples: '80' '21:udp' '11.0.0.0/24,20-23:TCP' '12.0.0.0/32:6000-6500,443' '{CLIENT_IP},22:TCP' "),
    type=[InboundTrafficRule],
)
inbound_rule_ns.add_parameter(
    "ingress_icmp",
    default=None,
    help="CIDR from which to allow ingress ICMP traffic to the head node. "
         "Specify 'none' to disable ICMP altogether.",
    parser=cidr_list
)

clustercreate_ns = ConfigNamespace("cluster.create")
clustercreate_ns.import_namespace(clustercreatelicense_ns)
clustercreate_ns.import_namespace(clustercreatepassword_ns)
clustercreate_ns.import_namespace(clustercreatewlm_ns)
clustercreate_ns.import_namespace(clusterprefix_ns)
clustercreate_ns.import_namespace(clustercreateconfirm_ns)
clustercreate_ns.import_namespace(clustercreatedisks_ns)
clustercreate_ns.import_namespace(inbound_rule_ns)
clustercreate_ns.import_namespace(nodes_ns)
clustercreate_ns.import_namespace(bright_setup_ns)

clustercreate_ns.add_parameter(
    "on_error",
    choices=["cleanup", "abort"],
    help="What to do on failure",
    help_choices={
        "cleanup": "Delete the cluster and clean up resources",
        "abort": "Do nothing and exit"
    }
)
clustercreate_ns.add_parameter(
    "head_node_type",
    flags=["-m"],
    help="The instance type must exist in the region you use.")
clustercreate_ns.add_parameter(
    "node_type",
    help="The instance type of compute nodes. It must exist in the region you use.")

clusterdelete_ns = ConfigNamespace("cluster.delete")
clusterdelete_ns.import_namespace(confirm_ns)
clusterdelete_ns.import_namespace(clusterprefix_ns)
clusterdelete_ns.add_positional_parameter(
    "name",
    help="Name of the cluster to delete",
    require_value=True)


clusterlist_ns = ConfigNamespace("cluster.list")
clusterlist_ns.add_parameter(
    "output_format",
    flags=["-f"],
    default="table",
    choices=["table", "csv", "value", "yaml"],
    help="Output format for lists")

sshconfig_ns = ConfigNamespace("sshconfig", "SSH local configuration")
sshconfig_ns.add_parameter(
    "ssh_config_path",
    help="Path to local ssh config to save COD cluster ssh configuration in.",
    default="~/.ssh/config",
)
sshconfig_ns.add_switch_parameter(
    "update_ssh_config",
    help="Updates the contents of ~/.ssh/config, this is used to maintain the local ssh configuration "
         "access with ssh, scp and related tools.",
)
sshconfig_ns.add_parameter(
    "ssh_config_alias_prefix",
    help="Prefix to be used when populating host entries for the cluster head nodes in the COD "
         "section of ~/.ssh/config. Default is ''.",
    default=""
)


cmd_debug_ns = ConfigNamespace("cmddebug", "Debug settings for CMDaemon")
cmd_debug_ns.add_switch_parameter(
    "cmd_debug",
    advanced=True,
    help="Enable debug mode on CMDaemon. The debug mode is enabled before CMDaemon is started for the first time. "
         "The affected subsystems can be customized with --cmd-debug-subsystems."
)
cmd_debug_ns.add_parameter(
    "cmd_debug_subsystems",
    default="*",
    help_varname="SUBSYSTEMS",
    advanced=True,
    help="Which CMDaemon subsystems (e.g: PROV, CMD, SERVICE) should have debug logging enabled. If --cmd-debug is "
         "set, SUBSYSTEMS is written to /cm/local/apps/cmd/etc/logging.cmd.conf on the head node and the default "
         "software image. Defaults to '*', i.e. all subsystems."
)

append_to_bashrc_ns = ConfigNamespace("cluster.create.headnode")
append_to_bashrc_ns.add_enumeration_parameter(
    "append_to_root_bashrc",
    default=[],
    help_varname="ENV=VAR",
    help="Lines to append to the /root/.bashrc file on the head node"
)

internal_net_ns = ConfigNamespace("cluster.internalnet")
internal_net_ns.add_parameter(
    "internal_cidr",
    default=cidr("10.141.0.0/16"),
    help="CIDR of the cluster's internal network.",
    parser=cidr,
)
internal_net_ns.add_parameter(
    "head_node_internal_ip",
    advanced=True,
    default=nth_ip_in_default_network(-2, "internal_cidr"),
    help_varname="IP",
    help=("IP address of the head node on internal network. "
          "If not set will be calculated from internal_cidr."),
    parser=ip,
    validation=ip_must_be_within_cidr("internal_cidr"),
)
internal_net_ns.add_parameter(
    "internal_mtu",
    type=int,
    help="MTU of the cluster's internal network. "
)

node_disk_setup_ns = ConfigNamespace("cluster.node")
node_disk_setup_ns.add_validation(require_at_least_one_to_be_set("node_disk_setup_path", "node_disk_setup"))
node_disk_setup_ns.add_parameter(
    "node_disk_setup_path",
    help_varname="PATH_TO_XML",
    help="Path to the XML file with the disk setup which is to be used for the nodes",
    validation=if_set_file_exists_and_readable,
)
node_disk_setup_ns.add_parameter(
    "node_disk_setup",
    default=DEFAULT_DISK_SETUP)


resolve_hostnames_ns = ConfigNamespace("cluster.create.headnode")
resolve_hostnames_ns.add_enumeration_parameter(
    "resolve_hostnames",
    default=[],
    help_varname="DOMAIN",
    advanced=True,
    help=("Hostname(s) which will be resolved by the tool during the cluster creation process. "
          "Resolved hostnames will be appended to /etc/hosts on the head node(s) and in the software image. "
          "This is useful when working around problems with DNS.")
)

timezone_ns = ConfigNamespace("cluster.create")
timezone_ns.add_parameter(
    "timezone",
    default="Europe/Amsterdam",
    help="Timezone of the cluster",
    validation=[may_not_equal_none, must_be_valid_timezone]
)


def get_system_config_files(additional_included_config_files: list[str] | None = None,
                            additional_system_config_files: list[str] | None = None) -> list[str]:
    return (additional_included_config_files or []) + \
        SYSTEM_CONFIG_FILES + \
        (additional_system_config_files or []) + \
        USER_CONFIG_FILES


def get_enforcing_config_files() -> list[str]:
    return ENFORCING_CONFIG_FILES
