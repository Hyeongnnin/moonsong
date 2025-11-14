import { Button } from "./ui/button";

interface HeaderProps {
  onNavigate: (page: 'landing' | 'login' | 'signup') => void;
  currentPage: string;
}

export function Header({ onNavigate, currentPage }: HeaderProps) {
  return (
    <header className="fixed top-0 left-0 right-0 bg-white border-b border-gray-200 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div 
            className="cursor-pointer"
            onClick={() => onNavigate('landing')}
          >
            <h1 className="text-blue-600">노타브</h1>
          </div>
          
          <nav className="hidden md:flex items-center gap-8">
            <a href="#service" className="text-gray-700 hover:text-blue-600 transition-colors">
              서비스 소개
            </a>
            <a href="#features" className="text-gray-700 hover:text-blue-600 transition-colors">
              주요 기능
            </a>
            <a href="#howto" className="text-gray-700 hover:text-blue-600 transition-colors">
              이용 방법
            </a>
          </nav>

          <div className="flex items-center gap-3">
            {currentPage !== 'login' && (
              <Button 
                variant="ghost"
                onClick={() => onNavigate('login')}
                className="text-gray-700"
              >
                로그인
              </Button>
            )}
            {currentPage !== 'signup' && (
              <Button 
                onClick={() => onNavigate('signup')}
                className="bg-blue-600 hover:bg-blue-700 text-white"
              >
                회원가입
              </Button>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
