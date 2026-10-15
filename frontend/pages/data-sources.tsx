import fs from 'fs';
import path from 'path';
import Head from 'next/head';

interface DataSourcesPageProps {
  bodyContent: string;
}

export async function getStaticProps() {
  const filePath = path.join(process.cwd(), 'data-sources.html');
  let bodyContent = '';
  try {
    const fullHtml = fs.readFileSync(filePath, 'utf8');
    const bodyMatch = fullHtml.match(/<body[^>]*>([\s\S]*)<\/body>/i);
    bodyContent = bodyMatch ? bodyMatch[1] : fullHtml;
  } catch (err) {
    console.error('Error reading data-sources.html in getStaticProps:', err);
    bodyContent = '<div class="page-container"><p>Loading Meteorological Data Sources...</p></div>';
  }

  return {
    props: {
      bodyContent,
    },
  };
}

export default function DataSourcesPage({ bodyContent }: DataSourcesPageProps) {
  return (
    <>
      <Head>
        <title>Meteorological Data Sources &amp; Provenance · Tamil Nadu Climate Platform</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      </Head>
      <div dangerouslySetInnerHTML={{ __html: bodyContent }} />
      <script
        dangerouslySetInnerHTML={{
          __html: `
            if (typeof loadDataSources === 'function') {
              loadDataSources();
            }
          `,
        }}
      />
    </>
  );
}
