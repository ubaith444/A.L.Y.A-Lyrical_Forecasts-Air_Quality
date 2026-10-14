import fs from 'fs';
import path from 'path';
import Head from 'next/head';

interface HomePageProps {
  bodyContent: string;
}

export async function getStaticProps() {
  const filePath = path.join(process.cwd(), 'index.html');
  let bodyContent = '';
  try {
    const fullHtml = fs.readFileSync(filePath, 'utf8');
    const bodyMatch = fullHtml.match(/<body[^>]*>([\s\S]*)<\/body>/i);
    bodyContent = bodyMatch ? bodyMatch[1] : fullHtml;
  } catch (err) {
    console.error('Error reading index.html in getStaticProps:', err);
    bodyContent = '<div class="app-shell"><p>Loading Tamil Nadu Climate Intelligence...</p></div>';
  }

  return {
    props: {
      bodyContent,
    },
  };
}

export default function HomePage({ bodyContent }: HomePageProps) {
  return (
    <>
      <Head>
        <title>Tamil Nadu Climate &amp; Forecast Intelligence Platform</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      </Head>
      <div dangerouslySetInnerHTML={{ __html: bodyContent }} />
    </>
  );
}
