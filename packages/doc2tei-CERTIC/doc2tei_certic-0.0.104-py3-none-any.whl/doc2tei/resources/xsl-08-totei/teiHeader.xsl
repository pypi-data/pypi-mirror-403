<?xml version="1.0" encoding="UTF-8"?>

<xsl:stylesheet version="2.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
  xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0"
  xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0"
  xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0"
  xmlns:draw="urn:oasis:names:tc:opendocument:xmlns:drawing:1.0"
  xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0"
  xmlns:xlink="http://www.w3.org/1999/xlink"
  xmlns:dc="http://purl.org/dc/elements/1.1/"
  xmlns:meta="urn:oasis:names:tc:opendocument:xmlns:meta:1.0"
  xmlns:number="urn:oasis:names:tc:opendocument:xmlns:datastyle:1.0"
  xmlns:svg="urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0" 
  xmlns:chart="urn:oasis:names:tc:opendocument:xmlns:chart:1.0" 
  xmlns:dr3d="urn:oasis:names:tc:opendocument:xmlns:dr3d:1.0" 
  xmlns:math="http://www.w3.org/1998/Math/MathML" 
  xmlns:form="urn:oasis:names:tc:opendocument:xmlns:form:1.0" 
  xmlns:script="urn:oasis:names:tc:opendocument:xmlns:script:1.0" 
  xmlns:config="urn:oasis:names:tc:opendocument:xmlns:config:1.0" 
  xmlns:ooo="http://openoffice.org/2004/office" 
  xmlns:ooow="http://openoffice.org/2004/writer" 
  xmlns:oooc="http://openoffice.org/2004/calc" 
  xmlns:dom="http://www.w3.org/2001/xml-events" 
  xmlns:xforms="http://www.w3.org/2002/xforms" 
  xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
  xmlns:rpt="http://openoffice.org/2005/report" 
  xmlns:of="urn:oasis:names:tc:opendocument:xmlns:of:1.2" 
  xmlns:xhtml="http://www.w3.org/1999/xhtml" 
  xmlns:grddl="http://www.w3.org/2003/g/data-view#" 
  xmlns:officeooo="http://openoffice.org/2009/office" 
  xmlns:tableooo="http://openoffice.org/2009/table" 
  xmlns:drawooo="http://openoffice.org/2010/draw" 
  xmlns:calcext="urn:org:documentfoundation:names:experimental:calc:xmlns:calcext:1.0" 
  xmlns:loext="urn:org:documentfoundation:names:experimental:office:xmlns:loext:1.0" 
  xmlns:field="urn:openoffice:names:experimental:ooo-ms-interop:xmlns:field:1.0" 
  xmlns:formx="urn:openoffice:names:experimental:ooxml-odf-interop:xmlns:form:1.0" 
  xmlns:css3t="http://www.w3.org/TR/css3-text/"
  xmlns="http://www.tei-c.org/ns/1.0"
  exclude-result-prefixes="#all">
    
<xsl:output method="xml" encoding="UTF-8" indent="no"/>
    
<xsl:template match="*:teiHeader">
    <teiHeader>
      <fileDesc>
        <titleStmt>
            <xsl:if test="//text:p[@text:style-name='TEI_title:sup']">
                <title type="sup"><xsl:apply-templates select="//text:p[@text:style-name='TEI_title:sup']" mode="teiHeader"/></title>
            </xsl:if>
          <title type="main">
              <xsl:copy-of select="//text:h[@text:outline-level='0']/@xml:lang"/>
              <xsl:choose>
                  <xsl:when test="//text:h[@text:outline-level='0' and @subtype='review']">
                      <xsl:apply-templates select="//text:h[@text:outline-level='0' and @subtype='review']//text:span[@text:style-name='TEI_reviewed_title-inline']//text()"/>
                  </xsl:when>
                  <xsl:otherwise>
                      <xsl:apply-templates select="//text:h[@text:outline-level='0']//text()[not(ancestor::text:note)][not(parent::text:span[@text:style-name='TEI_neutral-inline'])]" mode="teiHeader"/>
                  </xsl:otherwise>
              </xsl:choose>
          </title>
            <xsl:if test="//text:p[@text:style-name='TEI_title:sub']">
                <title type="sub"><xsl:apply-templates select="//text:p[@text:style-name='TEI_title:sub']" mode="teiHeader"/></title>
            </xsl:if>
            <xsl:if test="//text:p[contains(@text:style-name,'TEI_title:trl')]">
                <xsl:for-each select="//text:p[contains(@text:style-name,'TEI_title:trl')]">
                    <title type="trl">
                        <xsl:copy-of select="@xml:lang"/>
                        <xsl:apply-templates mode="teiHeader"/>
                    </title>
                </xsl:for-each>
            </xsl:if>
            <!-- bloc auteur -->
            <xsl:for-each-group select="//text:p[starts-with(@text:style-name,'TEI_author') or starts-with(@text:style-name,'TEI_editor')][not(ancestor::*:back) and @text:style-name!='TEI_author_section']" group-starting-with="text:p[starts-with(@text:style-name,'TEI_author:') or starts-with(@text:style-name,'TEI_editor:')]">
                <xsl:variable name="context">
                    <xsl:choose>
                        <xsl:when test="contains(@text:style-name,'TEI_authorities')">authorities</xsl:when>
                        <xsl:when test="contains(@text:style-name,'TEI_author')">author</xsl:when>
                        <xsl:when test="contains(@text:style-name,'TEI_editor')">editor</xsl:when>
                        <xsl:otherwise>undefined</xsl:otherwise>
                    </xsl:choose>
                </xsl:variable>
                <xsl:choose>
                    <!-- cas d'utilisation de TEI_section_auteur avec affiliation (coll. de cr ou encadrés) -->
                    <xsl:when test="@text:style-name='TEI_authority_affiliation'"/>
                    <xsl:when test="$context='authorities'">
                        <xsl:apply-templates select="./text:span[starts-with(@text:style-name,'TEI_author-inline:')]|./text:span[starts-with(@text:style-name,'TEI_editor-inline:')]" mode="teiHeader"/>
                        <xsl:if test="following-sibling::*[1][local-name()='p' and @text:style-name='TEI_authorities']"><xsl:apply-templates select="following-sibling::*[1][local-name()='p' and @text:style-name='TEI_authorities']/text:span[starts-with(@text:style-name,'TEI_author-inline:')]|following-sibling::*[1][local-name()='p' and @text:style-name='TEI_authorities']/text:span[starts-with(@text:style-name,'TEI_editor-inline:')]" mode="teiHeader"/></xsl:if>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:element name="{$context}">
                            <xsl:attribute name="role" select="substring-after(./@text:style-name,':')"/>
                            <xsl:apply-templates select="current-group()[not(contains(@text:style-name,'_biography'))]" mode="teiHeader"/>
                            <xsl:if test="current-group()/.[@text:style-name='TEI_authority_biography']">
                                <ref type="biography" target="{concat('#bio',format-number(position(),'00'))}"/>
                            </xsl:if>
<!--
                            <xsl:if test="ancestor::*:div[@type='review']">
                                <ref type="aut">
                                    <xsl:attribute name="target">
                                        <xsl:text>#div</xsl:text>
                                        <xsl:value-of select="count(preceding::*:div[ancestor::*:body])+1"/>
                                    </xsl:attribute>
                                </ref>
                            </xsl:if>
-->
                        </xsl:element>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:for-each-group>
<!-- auteur encadré -->
            <xsl:for-each select="//text:p[@text:style-name='TEI_section_author']">
                <author>
                    <persName>
                        <xsl:variable name="name"><xsl:value-of select="normalize-space(.)"/></xsl:variable>
                        <xsl:variable name="surname"><xsl:value-of select="tokenize($name,' ')[last()]"/></xsl:variable>
                        <forename><xsl:value-of select="normalize-space(substring-before($name,$surname))"/></forename>
                        <surname><xsl:value-of select="$surname"/></surname>
                    </persName>
                    <ref type="aut">
                        <xsl:attribute name="target">
                            <xsl:choose>
                                <xsl:when test="ancestor::*:floatingText">
                                    <xsl:text>#floatingText</xsl:text><xsl:value-of select="count(preceding::*:floatingText)+1"/>
                                </xsl:when>
                                <xsl:when test="ancestor::*:div[@type='review']">
                                    <xsl:text>#review</xsl:text><xsl:value-of select="count(preceding::*:div[@type='review'])+1"/>
                                </xsl:when>
                                <xsl:when test="ancestor::*:div[@type!='review']">
                                    <xsl:text>#div</xsl:text><xsl:number count="*[local-name()='div']" from="*:body[not(parent::*:floatingText)]" level="any"/>
                                </xsl:when>
                                <xsl:otherwise>
                                    <xsl:text>?</xsl:text>
                                </xsl:otherwise>
                            </xsl:choose>
                        </xsl:attribute>
                    </ref>
                </author>
            </xsl:for-each>
<!-- funder -->
             <xsl:for-each select="//text:p[starts-with(@text:style-name,'TEI_funder')]">
                 <funder>
                     <orgName><xsl:value-of select="text:span[@text:style-name='TEI_fundername_inline']"/></orgName>
                     <idno><xsl:value-of select="text:span[@text:style-name='TEI_funderref_inline']"/></idno>
                 </funder>
             </xsl:for-each>
        </titleStmt>
        <publicationStmt>
<!-- ## editorial_workflow ## -->
          <ab type="expression">
              <bibl>
                  <publisher></publisher>
                  <!-- Droits : expression de l'auteur (dispositifs légaux généraux)  -->
                  <availability>
                     <licence target="#"></licence>
                     <p></p>
                  </availability> 
              </bibl>
          </ab>
          <xsl:if test="//text:p[@text:style-name='TEI_date_reception'] or //text:p[@text:style-name='TEI_date_acceptance']">
              <ab type="editorial_workflow">
                  <xsl:if test="//text:p[@text:style-name='TEI_date_reception']">
                    <date type="received">
                        <xsl:variable name="rDate" select="substring(//text:p[@text:style-name='TEI_date_reception']/text:span[@text:style-name='TEI_date_normalised'],2,10)"/>
                        <xsl:variable name="rDateD" select="substring($rDate,1,2)"/>
                        <xsl:variable name="rDateM" select="substring($rDate,4,2)"/>
                        <xsl:variable name="rDateY" select="substring($rDate,7,4)"/>
                        <xsl:attribute name="when" select="concat($rDateY,'-',$rDateM,'-',$rDateD)"/>     
                        <xsl:value-of select="//text:p[@text:style-name='TEI_date_reception']/text()"/>
                    </date>
                  </xsl:if>
                  <xsl:if test="//text:p[@text:style-name='TEI_date_acceptance']">
                    <date type="accepted">
                        <xsl:variable name="aDate" select="substring(//text:p[@text:style-name='TEI_date_acceptance']/text:span[@text:style-name='TEI_date_normalised'],2,10)"/>
                        <xsl:variable name="aDateD" select="substring($aDate,1,2)"/>
                        <xsl:variable name="aDateM" select="substring($aDate,4,2)"/>
                        <xsl:variable name="aDateY" select="substring($aDate,7,4)"/>
                        <xsl:attribute name="when" select="concat($aDateY,'-',$aDateM,'-',$aDateD)"/>
                        <xsl:value-of select="//text:p[@text:style-name='TEI_date_acceptance']/text()"/>
                    </date>
                </xsl:if>
              </ab>
          </xsl:if>
<!-- blocs <ab> Métopes -->
            <ab type="book">
                <bibl>
                    <date type="publishing"></date>
                    <biblScope unit="page">
                        <xsl:variable name="pagination" select="//text:p[@text:style-name='TEI_pagination']"/>
                        <xsl:choose>
                            <xsl:when test="contains($pagination,'-')">
                                <xsl:attribute name="from"><xsl:value-of select="substring-before($pagination,'-')"/></xsl:attribute>
                                <xsl:attribute name="to" select="substring-after($pagination,'-')"/>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:attribute name="from"><xsl:value-of select="$pagination"/></xsl:attribute>
                            </xsl:otherwise>
                        </xsl:choose>
                     </biblScope>
                </bibl>
            </ab>
            <ab type="digital_download" subtype="PDF">
                <bibl>
                    <idno type="DOI" subtype="-"></idno>
                    <ref type="DOI"></ref>
                    <ref type="site"></ref>
                    <distributor></distributor>
                    <date type="publishing"></date>
                    <dim type="weight" unit="Mo" extent=""></dim>
                    <!-- Si contraire à ce qui est défini supra
                    <publisher></publisher> -->
                </bibl>
                <!-- Ajouter des métadonnées d'accessibilité 
                <desc type="??"></desc>-->
            </ab>
            <ab type="digital_download" subtype="EPUB">
                <bibl>
                    <idno type="ISBN-13"></idno>
                    <idno type="DOI" subtype="-"></idno>
                    <ref type="DOI"></ref>
                    <ref type="site"></ref>
                    <distributor></distributor>
                    <date type="publishing"></date>
                    <dim type="weight" unit="Ko" extent=""></dim>
                </bibl>
                    <!-- Mode d'accès par défaut : textual -->
                    <desc type="accessMode">textual</desc>
                    <!-- Mode d'accès 'visual' ajouté s'il y a des images. -->
                    <xsl:if test="ancestor::*:TEI//draw:image">
                        <desc type="accessMode">visual</desc>
                    </xsl:if>
                    <!-- Caractéristiques d'accessibilité présentes par défaut dans tous les ePubs Métopes : -->
                    <desc type="accessibilityFeature">ARIA</desc>
                    <desc type="accessibilityFeature">highContrastDisplay</desc>
                    <desc type="accessibilityFeature">readingOrder</desc>
                    <desc type="accessibilityFeature">structuralNavigation</desc>
                    <desc type="accessibilityFeature">tableOfContents</desc>
                    <desc type="accessibilityFeature">unlocked</desc>
                    <xsl:if test="count(ancestor::*:TEI//draw:image) = count(ancestor::*:TEI//draw:frame/svg:desc)">
                        <desc type="accessibilityFeature">alternativeText</desc>
                    </xsl:if>
                    <!-- Risques d'accessibilité (à vérifier par l'utilisateur) : -->
                    <desc subtype="soundHazard" type="accessibilityHazard">noSoundHazard</desc>
                    <desc subtype="flashingHazard" type="accessibilityHazard">noFlashingHazard</desc>
                    <desc subtype="motionSimulationHazard" type="accessibilityHazard">noMotionSimulationHazard</desc>

                    <!-- Mode d'accès suffisant (à vérifier par l'utilisateur) : "textual" par défaut, "textual,visual" lorsque toutes les images ne sont pas pourvues de texte alternatif. -->
                    <xsl:choose>
                        <xsl:when test="not(count(ancestor::*:TEI//draw:image) = count(ancestor::*:TEI//draw:frame/svg:desc))">
                            <desc type="accessModeSufficient">textual,visual</desc>
                        </xsl:when>
                        <xsl:otherwise>
                            <desc type="accessModeSufficient">textual</desc>
                        </xsl:otherwise>
                    </xsl:choose>
                    
                     <!-- Résumé d'accessibilité : -->
                    <desc type="accessibilitySummary">
 <!-- commenté car la ressource n'est pas sur le serveur : 
                        <xsl:variable name="mainLangTwoCars" select="substring-before($mainLang, '-')"/>
                        <xsl:apply-templates select="document('../../../xxe/common/i18n.xml')//*:entry[*:key='accessibilitySummaryContent']/*:text[@xml:lang = $mainLangTwoCars]/node()"/>
-->
</desc>
            </ab>
            <ab type="digital_online" subtype="HTML">
                <bibl>
                    <distributor><!--OpenEdition|Cairn.info|Érudit|Redalyc|Other--></distributor>
                    <name type="CMS"></name>
                    <idno type="DOI" subtype="-"></idno>
                    <ref type="DOI"></ref>
                    <ref type="site"></ref>
                    <date type="publishing"></date>
                    <date type="embargoend"></date>
                    <date type="early"></date>
                    <idno type="documentnumber">
                        <xsl:value-of select="//text:p[@text:style-name='TEI_document_number']"/>
                    </idno> <!--num ?--> 
                </bibl>
            </ab>
<!-- archeo…-->
            <xsl:if test="following::text:p[starts-with(@text:style-name,'TEI_archeoART')]">
				<ab subtype="archeo">
					<idno>
						<xsl:attribute name="type" select="substring-after(following::text:p[starts-with(@text:style-name,'TEI_archeoART_IDmission:EFA')]/@text:style-name,':')"/>
						<xsl:value-of select="substring-after(following::text:p[starts-with(@text:style-name,'TEI_archeoART_IDmission:EFA')]/text(),': ')"/>
					</idno>
					<xsl:variable name="dateOP" select="substring-after(following::text:p[@text:style-name='TEI_archeoART_date'],': ')"/>
					<xsl:analyze-string select="$dateOP" regex="\d{{4}}">
                            <xsl:matching-substring>
                                <date>
                                    <xsl:value-of select="."/>
                                </date>
                            </xsl:matching-substring>
                            <xsl:non-matching-substring/>
                        </xsl:analyze-string>
					<name type="nature_op"><term><xsl:value-of select="substring-after(following::text:p[starts-with(@text:style-name,'TEI_archeoCHR_fieldwork_method')]/text(),': ')"/></term></name>
				</ab>
			</xsl:if>
        </publicationStmt>
        <sourceDesc>
            <bibl></bibl>
        </sourceDesc>
      </fileDesc>
      <encodingDesc>
        <xsl:if test="not(//meta:user-defined[@meta:name='tplVersion'])">
            <ERROR>
                <xsl:text>WRONG WORD TEMPLATE USED</xsl:text>
          </ERROR>
        </xsl:if>
        <appInfo>
            <application ident="Word-tpl">
                <xsl:attribute name="version">
                    <xsl:value-of select="//meta:user-defined[@meta:name='tplVersion']"/>
                </xsl:attribute>
                <label>Word template</label>
                <desc>Version of MS Word template used</desc>
                <!-- todo : lien vers le code publié -->
                <ref target="#"/>
            </application>
            <application version="0.0.104">
                <xsl:attribute name="ident" select="concat('circe-',$source)"/>
                <label>Circé</label>
                <desc>Document converted into TEI using Circé application (doc2tei pipeline).</desc>
                <!-- todo : lien vers le code publié -->
                <ref target="#"/>
            </application>
                    <application version="1.0" ident="commons-publishing-metopes">
                        <label>Schéma XML-TEI</label>
                        <desc>Commons Publishing Métopes 1.0</desc>
                        <!-- todo : lien vers le code publié -->
                        <ref target="#"/>
                    </application>
        </appInfo>
    <!-- génération conditionnelle du tagsDecl : ajouter test table -->
          <xsl:if test="//text:list or //*[starts-with(@rendition,'#')]">
            <tagsDecl>
            <xsl:if test="//*[contains(@rendition,'#rtl')]">
                <rendition scheme="css" xml:id="rtl">direction:rtl;</rendition>
            </xsl:if>
            <!-- traitement exhaustif cas par cas car syntaxe des instructions CSS parfois différentes de la valeur de l'@rendition -->
            <xsl:if test="//*[contains(@rendition,'#start')]">
                <rendition scheme="css" xml:id="start">
                    <xsl:text>text-align:start;</xsl:text>
                </rendition>
            </xsl:if>
            <xsl:if test="//*[contains(@rendition,'#center')]">
                <rendition scheme="css" xml:id="center">
                    <xsl:text>text-align:center;</xsl:text>
                </rendition>
            </xsl:if>
            <xsl:if test="//*[contains(@rendition,'#justify')]">
                <rendition scheme="css" xml:id="justify">
                    <xsl:text>text-align:justify;</xsl:text>
                </rendition>
            </xsl:if>
            <xsl:if test="//*[contains(@rendition,'#end')]">
                <rendition scheme="css" xml:id="end">
                    <xsl:text>text-align:end;</xsl:text>
                </rendition>
            </xsl:if>
            <!-- liste des valeurs : disc, square, circle, endash | decimal, lower-roman, upper-roman, lower-alpha, upper-alpha -->
              <xsl:if test="//text:list/@style:num-format='1'"><rendition scheme="css" xml:id="list-decimal">list-style-type:decimal;</rendition></xsl:if>
              <xsl:if test="//text:list/@style:num-format='i'"><rendition scheme="css" xml:id="list-lower-roman">list-style-type:lower-roman;</rendition></xsl:if>
              <xsl:if test="//text:list/@style:num-format='I'"><rendition scheme="css" xml:id="list-upper-roman">list-style-type:upper-roman;</rendition></xsl:if>
              <xsl:if test="//text:list/@style:num-format='a'"><rendition scheme="css" xml:id="list-lower-alpha">list-style-type:lower-alpha;</rendition></xsl:if>
              <xsl:if test="//text:list/@style:num-format='A'"><rendition scheme="css" xml:id="list-upper-alpha">list-style-type:upper-alpha;</rendition></xsl:if>
              <xsl:if test="//text:list/@text:bullet-char='■'"><rendition scheme="css" xml:id="list-square">list-style-type:square;</rendition></xsl:if>
              <xsl:if test="//text:list/@text:bullet-char='○'"><rendition scheme="css" xml:id="list-circle">list-style-type:circle;</rendition></xsl:if>
              <xsl:if test="//text:list/@text:bullet-char='●'"><rendition scheme="css" xml:id="list-disc">list-style-type:disc;</rendition></xsl:if>
              <xsl:if test="//text:list/@text:bullet-char='-'"><rendition scheme="css" xml:id="list-ndash">list-style-type:"–";</rendition></xsl:if>
              <!-- définir un comportement si autre cas rencontré ? -->
            </tagsDecl>
        </xsl:if>
    <!-- rendu des cellules de tableaux -->
        <xsl:if test="//table:table">
            <tagsDecl>
                <xsl:for-each select="//style:style[@style:family='table-cell']">
                    <xsl:variable name="cellKey">
                        <xsl:analyze-string select="@style:name" regex="(\d+)\.[A-Z](\d+)">
                          <xsl:matching-substring>
                              <xsl:value-of select="."/>
                          </xsl:matching-substring>
                          <xsl:non-matching-substring/>
                        </xsl:analyze-string>
                    </xsl:variable>
                    <rendition scheme="css">
                        <xsl:attribute name="xml:id">
                            <xsl:value-of select="concat('Cell',$cellKey)"/>
                        </xsl:attribute>
                        <xsl:variable name="cellRendition">
                            <xsl:if test="child::style:table-cell-properties/@fo:border">
                                <xsl:value-of select="concat(string-join((local-name(child::style:table-cell-properties/@fo:border),child::style:table-cell-properties/@fo:border), ':'),'; ')"/>
                            </xsl:if>
                            <xsl:if test="child::style:table-cell-properties/@fo:border-top">
                                <xsl:value-of select="concat(string-join((local-name(child::style:table-cell-properties/@fo:border-top),child::style:table-cell-properties/@fo:border-top), ':'),'; ')"/>
                            </xsl:if>
                            <xsl:if test="child::style:table-cell-properties/@fo:border-right">
                                <xsl:value-of select="concat(string-join((local-name(child::style:table-cell-properties/@fo:border-right),child::style:table-cell-properties/@fo:border-right), ':'),'; ')"/>
                            </xsl:if>
                            <xsl:if test="child::style:table-cell-properties/@fo:border-bottom">
                                <xsl:value-of select="concat(string-join((local-name(child::style:table-cell-properties/@fo:border-bottom),child::style:table-cell-properties/@fo:border-bottom), ':'),'; ')"/>
                            </xsl:if>
                            <xsl:if test="child::style:table-cell-properties/@fo:border-left">
                                <xsl:value-of select="concat(string-join((local-name(child::style:table-cell-properties/@fo:border-left),child::style:table-cell-properties/@fo:border-left), ':'),'; ')"/>
                            </xsl:if>
                            <xsl:if test="child::style:table-cell-properties/@fo:background-color">
                                <xsl:value-of select="concat(string-join((local-name(child::style:table-cell-properties/@fo:background-color),child::style:table-cell-properties/@fo:background-color), ':'),'; ')"/>
                            </xsl:if>
                            <xsl:if test="child::style:table-cell-properties/@style:vertical-align">
                                <xsl:value-of select="concat(string-join((local-name(child::style:table-cell-properties/@style:vertical-align),child::style:table-cell-properties/@style:vertical-align), ':'),'; ')"/>
                            </xsl:if>
                        </xsl:variable>
                        <xsl:value-of select="$cellRendition"/>
                    </rendition>
                </xsl:for-each>
            </tagsDecl>
        </xsl:if>
        <editorialDecl>
            <normalization rendition="notes">
                <p rendition="note" select="restart"/>
                <p rendition="table" select="restart"/>
                <p rendition="annexe" select="restart"/>
                <p rendition="floatingText" select="restart"/>
            </normalization>
        </editorialDecl>
      </encodingDesc>
      <profileDesc>
        <langUsage>
          <language>
              <!-- diff Métopes/OE : combien de code de langue -->
              <xsl:attribute name="ident">
                  <xsl:choose>
                      <xsl:when test="$source='Metopes'">
                          <xsl:value-of select="$mainLang"/>
                      </xsl:when>
                      <xsl:otherwise>
                          <xsl:value-of select="//text:p[@text:style-name='TEI_language']"/>
                      </xsl:otherwise>
                  </xsl:choose>
              </xsl:attribute>
          </language>
        </langUsage>
        <!-- mots-clés -->
        <xsl:if test="//text:p[starts-with(@text:style-name,'TEI_keywords')]">
            <textClass>
                <xsl:for-each select="//text:p[starts-with(@text:style-name,'TEI_keywords')]">
                    <xsl:call-template name="keywords"/>
                </xsl:for-each>
            </textClass>
        </xsl:if>
      </profileDesc>
      <revisionDesc>
          <listChange>
              <change type="creation">
                  <xsl:attribute name="when">
                      <xsl:value-of select="format-date(current-date(), '[Y0001]-[M01]-[D01]')"/>
                  </xsl:attribute>
                  <xsl:text>XML-TEI file creation</xsl:text>
              </change>
          </listChange>
      </revisionDesc>
    </teiHeader>
</xsl:template>

<xsl:template match="text:h[@text:outline-level='0']" mode="front">
    <xsl:apply-templates/>
</xsl:template>
    
<xsl:template match="text:p[starts-with(@text:style-name,'TEI_author:')]" mode="teiHeader">
    <persName>    
        <xsl:variable name="nameString"><xsl:value-of select=".//text()[not(parent::text:span[@text:style-name='TEI_neutral-inline'])]"/></xsl:variable>
        <xsl:variable name="name"><xsl:value-of select="normalize-space($nameString)"/></xsl:variable>
        <xsl:variable name="surname"><xsl:value-of select="tokenize($name,' ')[last()]"/></xsl:variable>
        <forename><xsl:value-of select="normalize-space(substring-before($name,$surname))"/></forename>
        <surname><xsl:value-of select="$surname"/></surname>
    </persName>
</xsl:template>
    
<xsl:template match="text:p[starts-with(@text:style-name,'TEI_editor:')]" mode="teiHeader">
    <persName>
        <xsl:variable name="nameString"><xsl:value-of select=".//text()[not(parent::text:span[@text:style-name='TEI_neutral-inline'])]"/></xsl:variable>
        <xsl:variable name="name"><xsl:value-of select="normalize-space($nameString)"/></xsl:variable>
        <xsl:variable name="surname"><xsl:value-of select="tokenize($name,' ')[last()]"/></xsl:variable>
        <forename><xsl:value-of select="normalize-space(substring-before($name,$surname))"/></forename>
        <surname><xsl:value-of select="$surname"/></surname>
    </persName>
</xsl:template>
    
<xsl:template match="text:p[@text:style-name='TEI_authority_affiliation']" mode="teiHeader">
    <affiliation>
        <orgName>
            <xsl:apply-templates select=".//text()[not(parent::text:span[@text:style-name='TEI_mail-inline']) and not(parent::text:span[@text:style-name='TEI_neutral-inline'])]" mode="teiHeader"/>
        </orgName>
    </affiliation>
</xsl:template>
    
<xsl:template match="text:p[@text:style-name='TEI_authority_mail']" mode="teiHeader">
    <email>
        <xsl:apply-templates mode="teiHeader"/>
    </email>
</xsl:template>

<xsl:template match="text:span[starts-with(@text:style-name,'TEI_author-inline:')]|text:span[starts-with(@text:style-name,'TEI_editor-inline:')]" mode="teiHeader">
    <xsl:variable name="context">
        <xsl:choose>
            <xsl:when test="contains(@text:style-name,'TEI_author')">author</xsl:when>
            <xsl:when test="contains(@text:style-name,'TEI_editor')">editor</xsl:when>
            <xsl:otherwise>undefined</xsl:otherwise>
        </xsl:choose>
    </xsl:variable>
    <xsl:element name="{$context}">
        <xsl:attribute name="role" select="substring-after(./@text:style-name,':')"/>
        <persName>
            <xsl:variable name="name"><xsl:value-of select="normalize-space(.)"/></xsl:variable>
            <xsl:variable name="surname"><xsl:value-of select="tokenize($name,' ')[last()]"/></xsl:variable>
            <forename><xsl:value-of select="normalize-space(substring-before($name,$surname))"/></forename>
            <surname><xsl:value-of select="$surname"/></surname>
        </persName>
        <!-- !! faut-il créer les éléments affiliation et mail ici par défaut ? si style de caractères, alors pas de déduction possible ? -->
        <xsl:if test="following::text:p[@text:style-name='TEI_authority_affiliation'] or following::text:span[@text:style-name='TEI_affiliation-inline']">
            <affiliation><ref type="affiliation" target="#"/></affiliation>
        </xsl:if>
        <xsl:if test="following::text:p[@text:style-name='TEI_authority_mail'] or following::text:span[@text:style-name='TEI_mail-inline']">
            <xsl:choose>
                <xsl:when test="following::text:span[@text:style-name='TEI_mail-inline']">
                    <email>
                        <ref target="#" type="email"/>
                    </email>
                </xsl:when>
                <xsl:when test="following::text:p[@text:style-name='TEI_authority_mail'] and not(following::text:span[@text:style-name='TEI_mail-inline'])">
                    <email>
                        <ref target="#" type="email"/>
                    </email>
                </xsl:when>
                <xsl:otherwise>
                    <email/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:if>
    </xsl:element>
</xsl:template>
    
<xsl:template match="text:p[@text:style-name='TEI_authority_affiliation']" mode="preserve">
    <xsl:apply-templates/>
</xsl:template>

<xsl:template name="keywords">
    <keywords>
        <xsl:copy-of select="@xml:lang"/>
        <xsl:if test="ends-with(@text:style-name,'keywords')">
            <xsl:attribute name="scheme">keyword</xsl:attribute>
        </xsl:if>
        <xsl:if test="contains(@text:style-name,'keywords_subjects:')">
            <xsl:attribute name="scheme" select="substring-after(@text:style-name,'keywords_subjects:')"/>
        </xsl:if>
        
        <list>
            <xsl:variable name="list">
                <xsl:choose>
                    <xsl:when test="contains(.,':')">
                        <xsl:value-of select="substring-after(., ': ')"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="."/>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:variable>
            <xsl:choose>
            <!-- personcited -->
                <xsl:when test="contains(@text:style-name,'personcited')">
                    <xsl:call-template name="keyWordsListPC">
                        <xsl:with-param name="list">
                            <xsl:value-of select="$list"/>
                        </xsl:with-param>
                    </xsl:call-template>
                </xsl:when>
            <!-- autres listes de mc -->
                <xsl:otherwise>
                    <xsl:call-template name="keyWordsList">
                        <xsl:with-param name="list">
                            <xsl:value-of select="$list"/>
                        </xsl:with-param>
                    </xsl:call-template>
                </xsl:otherwise>
            </xsl:choose>         
        </list>
    </keywords>
</xsl:template>

<xsl:template name="keyWordsList">
    <xsl:param name="list"/>
        <xsl:variable name="separator">
            <xsl:choose>
              <xsl:when test="contains($list,'،')">
                <xsl:text>،</xsl:text>
              </xsl:when>
              <xsl:otherwise>
                <xsl:text>,</xsl:text>
              </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:variable name="first" select="substring-before($list, $separator)" />
        <xsl:variable name="remaining" select="substring-after($list, $separator)" />
    <xsl:choose>
        <xsl:when test="$first">
            <item><xsl:value-of select="$first"/></item>
            <xsl:if test="$remaining">
                <xsl:call-template name="keyWordsList">
                    <xsl:with-param name="list" select="$remaining" />
                </xsl:call-template>
            </xsl:if>
        </xsl:when>
        <xsl:otherwise>
            <item><xsl:value-of select="$list"/></item>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>
    
<xsl:template name="keyWordsListPC">
    <xsl:param name="list"/>
    <xsl:variable name="first" select="normalize-space(substring-before($list, ', '))" />
    <xsl:variable name="remaining" select="substring-after($list, ', ')" />
    <xsl:choose>
        <xsl:when test="$first">
            <xsl:variable name="surname"><xsl:value-of select="tokenize($first,' ')[last()]"/></xsl:variable>
            <xsl:variable name="persname"><xsl:value-of select="substring-before($first,$surname)"/></xsl:variable>
            <item>
                <persName>
                    <xsl:if test="$persname!=''">
                        <forename>
                            <xsl:value-of select="normalize-space($persname)"/>
                        </forename>
                    </xsl:if>
                    <surname>
                        <xsl:value-of select="$surname"/>
                    </surname>
                </persName>
            </item>
            <xsl:if test="$remaining">
                <xsl:call-template name="keyWordsListPC">
                    <xsl:with-param name="list" select="$remaining" />
                </xsl:call-template>
            </xsl:if>
        </xsl:when>
        <xsl:otherwise>
            <xsl:variable name="surname"><xsl:value-of select="tokenize(normalize-space($list),' ')[last()]"/></xsl:variable>
            <xsl:variable name="persname"><xsl:value-of select="normalize-space(substring-before($list,$surname))"/></xsl:variable>
            <item>
                <persName>
                    <xsl:if test="$persname!=''">
                        <forename>
                               <xsl:value-of select="$persname"/>
                        </forename>
                    </xsl:if>
                    <surname>
                        <xsl:value-of select="$surname"/>
                    </surname>
                </persName>
            </item>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>
    
<xsl:template match="//text:p[@text:style-name='TEI_date_reception']"/>
<xsl:template match="//text:p[@text:style-name='TEI_date_acceptance']"/>
<xsl:template match="//text:p[@text:style-name='TEI_language']"/>
<xsl:template match="//text:p[@text:style-name='TEI_pagination']"/>
<xsl:template match="//text:p[@text:style-name='TEI_document_number']"/>
    
<xsl:template match="//text:span[@text:style-name='TEI_neutral-inline']" mode="teiHeader"></xsl:template>
<xsl:template match="//text:span[@text:style-name='TEI_neutral-inline']"><xsl:apply-templates/></xsl:template>
    
<!--
<xsl:template match="//text:p[@text:style-name='TEI_authority_biography']">
    <p><xsl:apply-templates/></p>
</xsl:template>    
-->
    
</xsl:stylesheet>