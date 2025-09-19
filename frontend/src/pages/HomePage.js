
import { Link } from "react-router-dom";
import Button from "../components/Button";
import Card from "../components/Card";


export default function HomePage() {
  return (
    <div className="grid gap-6 md:grid-cols-2">
      <Card className="p-6">
        <h2 className="mb-2 text-xl font-semibold">Welcome</h2>
        <p className="text-sm text-zinc-400">Use Browse to filter the catalog, open a movie for details, or try Trending/Top Rated. Set your API base via the API button.</p>
      </Card>
      <Card className="p-6">
        <h3 className="mb-2 text-lg font-semibold">Quick Links</h3>
        <div className="flex flex-wrap gap-2">
          <Link to="/browse"><Button variant="secondary">Browse</Button></Link>
          <Link to="/trending"><Button variant="secondary">Trending</Button></Link>
          <Link to="/top-rated"><Button variant="secondary">Top Rated</Button></Link>
          <Link to="/recs"><Button variant="secondary">Recommendations</Button></Link>
          <Link to="/sign-in"><Button variant="secondary">Sign In</Button></Link>
          <Link to="/sign-up"><Button variant="secondary">Sign Up</Button></Link>
        </div>
      </Card>
    </div>
  );
}
