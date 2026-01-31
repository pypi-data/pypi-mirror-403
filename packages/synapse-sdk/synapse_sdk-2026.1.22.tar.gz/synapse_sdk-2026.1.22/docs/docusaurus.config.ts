// ./docs/docusaurus.config.ts
import { themes as prismThemes } from 'prism-react-renderer';
import type { Config } from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';
import path from 'path';
import tailwindPlugin from './src/plugins/tailwind-config.cjs';

const config: Config = {
  title: 'Synapse SDK',
  tagline: 'Build ML and data processing plugins',
  favicon: 'img/favicon.ico',

  // Set the production url of your site here
  url: 'https://www.synapse.sh',
  baseUrl: '/',

  organizationName: 'datamaker-kr',
  projectName: 'synapse-sdk-v2',

  onBrokenLinks: 'throw',

  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
          routeBasePath: '/',
        },
        blog: false, // Disable blog
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],
  plugins: [
    tailwindPlugin,
    require.resolve('docusaurus-lunr-search'),
    [
      '@signalwire/docusaurus-plugin-llms-txt',
      {
        ui: {
          copyPageContent: {
            buttonLabel: 'Copy Page',
            display: {
              docs: true,
            },
          },
        },
      },
    ],
  ],
  themes: ['@docusaurus/theme-mermaid', '@signalwire/docusaurus-theme-llms-txt'],
  markdown: {
    mermaid: true,
    hooks: {
      onBrokenMarkdownLinks: 'warn',
    },
  },



  themeConfig: {
    announcementBar: {
      id: 'work_in_progress',
      content: '🚧 This documentation is a work in progress.',
      backgroundColor: '#fef3c7',
      textColor: '#92400e',
      isCloseable: false,
    },
    navbar: {
      title: 'Synapse SDK',
      logo: {
        alt: 'Synapse SDK Logo',
        src: 'img/logo.png',
      },
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'tutorialSidebar',
          position: 'left',
          label: 'Documentation',
        },
        {
          href: 'https://github.com/datamaker-kr/synapse-sdk-v2',
          label: 'GitHub',
          position: 'right',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Docs',
          items: [
            {
              label: 'Introduction',
              to: '/introduction',
            },
            {
              label: 'Quickstart',
              to: '/quickstart',
            },
            {
              label: 'API Reference',
              to: '/api',
            },
          ],
        },
        {
          title: 'Community',
          items: [
            {
              label: 'GitHub',
              href: 'https://github.com/datamaker-kr/synapse-sdk-v2',
            },
          ],
        },
        {
          title: 'More',
          items: [
            {
              label: 'Blog',
              href: 'https://www.datamaker.io/blog',
            },
            {
              label: 'Datamaker',
              href: 'https://www.datamaker.io',
            },
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} Datamaker.`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
      additionalLanguages: ['python', 'bash'],
    },
    mermaid: {
      theme: { light: 'neutral', dark: 'dark' },
    },
  } satisfies Preset.ThemeConfig,
};

export default config;