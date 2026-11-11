# Publicar sem carregar o histórico antigo

Esta pasta foi preparada sem `.git`, dados reais, credenciais, backups ou app legado.
Nenhum repositório foi criado remotamente. Nenhuma visibilidade foi alterada.

1. Revogue/rotacione a credencial exposta no projeto antigo. Privatizá-lo não invalida a chave.
2. Revise README, identidade visual, arquivos e direitos de autoria/coautoria.
3. Rode os testes, configure sua chave fora da pasta e valide o Qwen e a busca real.
4. Grave uma demonstração com dados fictícios e registre limites/resultados reais.
5. Crie um repositório NOVO (não fork do antigo), por exemplo `Ayla-Assistant`, e use esta pasta
   como raiz. GitHub Desktop permite criar/publicar um repositório a partir dela. Revise a lista
   de arquivos do primeiro commit antes de publicar como público. Não adicione a pasta antiga
   inteira nem copie seu diretório `.git`.
6. Depois confira o repositório em uma janela deslogada. Código público não significa servidor
   público; mantenha o backend somente em 127.0.0.1.

O atalho de exportação não garante que alterações futuras não introduzirão segredos. .gitignore
não remove arquivos já rastreados. Segredos pertencem à configuração do usuário, não ao commit.

Fonte: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository
